from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio

from models import (
    get_db, Hearing, HearingResponse, HearingCreate,
    Recording, Transcription, TranscriptionSegment, SpeakerSegment,
    Report, ReportResponse
)
from audio_processing import AudioProcessingPipeline
from ai import SummaryGenerator
from notifications import EmailNotificationService

router = APIRouter()


@router.post("", response_model=HearingResponse)
async def create_hearing(hearing: HearingCreate, db: Session = Depends(get_db)):
    db_hearing = Hearing(**hearing.model_dump())
    db.add(db_hearing)
    db.commit()
    db.refresh(db_hearing)
    return db_hearing


@router.get("", response_model=List[HearingResponse])
async def list_hearings(
    status: Optional[str] = None,
    district: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Hearing)

    if status:
        query = query.filter(Hearing.status == status)
    if district:
        query = query.filter(Hearing.district == district)

    hearings = query.order_by(Hearing.scheduled_at.desc()).offset(skip).limit(limit).all()
    return hearings


@router.get("/{hearing_id}", response_model=HearingResponse)
async def get_hearing(hearing_id: int, db: Session = Depends(get_db)):
    hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
    if not hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")
    return hearing


@router.post("/{hearing_id}/process")
async def process_hearing(
    hearing_id: int,
    background_tasks: BackgroundTasks,
    reference_microphone_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
    if not hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")

    recordings = db.query(Recording).filter(Recording.hearing_id == hearing_id).all()
    if not recordings:
        raise HTTPException(status_code=400, detail="No recordings found for this hearing")

    hearing.status = "processing"
    db.commit()

    background_tasks.add_task(
        process_hearing_background,
        hearing_id,
        reference_microphone_id
    )

    return {
        "message": "Processing started in background",
        "hearing_id": hearing_id,
        "status": "processing"
    }


async def process_hearing_background(
    hearing_id: int,
    reference_microphone_id: Optional[str] = None
):
    from models.database import SessionLocal

    db = SessionLocal()
    try:
        hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
        recordings = db.query(Recording).filter(Recording.hearing_id == hearing_id).all()

        pipeline = AudioProcessingPipeline()
        pipeline_result = await pipeline.process_hearing_recordings(
            hearing_id=hearing_id,
            recordings=recordings,
            reference_microphone_id=reference_microphone_id
        )

        all_segments = []
        for rec in recordings:
            transcription = db.query(Transcription).filter(
                Transcription.recording_id == rec.id
            ).first()
            if transcription:
                speaker_segments = db.query(SpeakerSegment).filter(
                    SpeakerSegment.recording_id == rec.id
                ).all()

                for seg in transcription.segments:
                    speaker_info = get_speaker_for_segment(
                        seg.start_time, seg.end_time, speaker_segments
                    )
                    all_segments.append({
                        'start_time': seg.start_time,
                        'end_time': seg.end_time,
                        'text': seg.text,
                        'speaker_id': speaker_info.get('speaker_id'),
                        'speaker_role': speaker_info.get('speaker_role')
                    })

        all_segments.sort(key=lambda x: x['start_time'])

        noise_levels = [r.noise_level for r in recordings if r.noise_level]
        noise_data = {
            'recordings_count': len(recordings),
            'average_level': sum(noise_levels) / len(noise_levels) if noise_levels else 0,
            'max_level': max(noise_levels) if noise_levels else 0,
            'locations': [r.location_name for r in recordings]
        }

        summary_generator = SummaryGenerator()
        hearing_data = {
            'title': hearing.title,
            'description': hearing.description,
            'district': hearing.district,
            'scheduled_at': hearing.scheduled_at.isoformat() if hearing.scheduled_at else None
        }

        summary = summary_generator.generate_hearing_summary(
            hearing_data=hearing_data,
            transcript_segments=all_segments,
            noise_data=noise_data
        )

        markdown_report = summary_generator.generate_markdown_report(
            summary=summary,
            hearing_data=hearing_data,
            transcript_segments=all_segments
        )

        report = Report(
            hearing_id=hearing_id,
            summary=summary.summary,
            key_points=summary.key_points,
            zoning_recommendations=summary.zoning_recommendations,
            noise_level_analysis=summary.noise_level_analysis,
            full_markdown=markdown_report
        )
        db.add(report)

        hearing.status = "completed"
        db.commit()
        db.refresh(report)

        email_service = EmailNotificationService()
        email_results = await email_service.send_hearing_report(
            report_id=report.id,
            hearing_title=hearing.title,
            markdown_content=markdown_report,
            priority_level=summary.priority_level
        )

        if email_results.get('env_dept'):
            report.sent_to_env_dept = True
        if email_results.get('planning'):
            report.sent_to_planning = True
        db.commit()

    except Exception as e:
        hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
        if hearing:
            hearing.status = "failed"
            db.commit()
        print(f"Error processing hearing {hearing_id}: {e}")
    finally:
        db.close()


def get_speaker_for_segment(start_time, end_time, speaker_segments):
    best_match = None
    max_overlap = 0

    for speaker_seg in speaker_segments:
        overlap_start = max(start_time, speaker_seg.start_time)
        overlap_end = min(end_time, speaker_seg.end_time)
        overlap = max(0, overlap_end - overlap_start)

        if overlap > max_overlap:
            max_overlap = overlap
            best_match = speaker_seg

    if best_match:
        return {
            'speaker_id': best_match.speaker_id,
            'speaker_role': best_match.speaker_role
        }
    return {'speaker_id': None, 'speaker_role': None}


@router.post("/{hearing_id}/recordings/{recording_id}")
async def add_recording_to_hearing(
    hearing_id: int,
    recording_id: int,
    db: Session = Depends(get_db)
):
    hearing = db.query(Hearing).filter(Hearing.id == hearing_id).first()
    if not hearing:
        raise HTTPException(status_code=404, detail="Hearing not found")

    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    recording.hearing_id = hearing_id
    db.commit()
    db.refresh(recording)

    return {"message": "Recording added to hearing", "recording_id": recording_id}


@router.get("/{hearing_id}/report", response_model=ReportResponse)
async def get_hearing_report(hearing_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.hearing_id == hearing_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found for this hearing")
    return report
