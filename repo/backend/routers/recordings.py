from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from models import get_db, Recording, RecordingResponse, RecordingCreate, TranscriptionResponse
from config import settings

router = APIRouter()


@router.post("/upload", response_model=RecordingResponse)
async def upload_recording(
    file: UploadFile = File(...),
    microphone_id: str = Query(...),
    location_name: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    recorded_at: datetime = Query(...),
    db: Session = Depends(get_db)
):
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    recording = Recording(
        filename=file.filename,
        file_path=file_path,
        microphone_id=microphone_id,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
        recorded_at=recorded_at,
        status="uploaded"
    )

    db.add(recording)
    db.commit()
    db.refresh(recording)

    return recording


@router.get("", response_model=List[RecordingResponse])
async def list_recordings(
    microphone_id: Optional[str] = None,
    status: Optional[str] = None,
    hearing_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Recording)

    if microphone_id:
        query = query.filter(Recording.microphone_id == microphone_id)
    if status:
        query = query.filter(Recording.status == status)
    if hearing_id:
        query = query.filter(Recording.hearing_id == hearing_id)

    recordings = query.order_by(Recording.recorded_at.desc()).offset(skip).limit(limit).all()
    return recordings


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(recording_id: int, db: Session = Depends(get_db)):
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    return recording


@router.get("/{recording_id}/transcription", response_model=TranscriptionResponse)
async def get_recording_transcription(recording_id: int, db: Session = Depends(get_db)):
    from models import Transcription

    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    transcription = db.query(Transcription).filter(
        Transcription.recording_id == recording_id
    ).first()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return transcription


@router.put("/{recording_id}/status")
async def update_recording_status(
    recording_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db)
):
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")

    recording.status = status
    db.commit()
    db.refresh(recording)

    return {"message": "Status updated", "status": recording.status}
