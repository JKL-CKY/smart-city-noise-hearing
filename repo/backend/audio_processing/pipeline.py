import os
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .time_alignment import AudioTimeAligner, estimate_noise_level
from .transcriber import WhisperTranscriber
from .speaker_diarization import PyannoteDiarizer
from config import settings
from models import Recording, Transcription, TranscriptionSegment, SpeakerSegment
from models.database import SessionLocal


class AudioProcessingPipeline:
    def __init__(self):
        self.aligner = AudioTimeAligner()
        self.transcriber = WhisperTranscriber()
        self.diarizer = PyannoteDiarizer()

    async def process_hearing_recordings(
        self,
        hearing_id: int,
        recordings: List[Recording],
        reference_microphone_id: Optional[str] = None
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            for rec in recordings:
                rec.status = "processing"
            db.commit()

            recording_paths = [
                {
                    'file_path': rec.file_path,
                    'microphone_id': rec.microphone_id
                }
                for rec in recordings
            ]

            if reference_microphone_id:
                self.aligner.reference_microphone_id = reference_microphone_id

            alignment_result = self.aligner.align_recordings(recording_paths)

            output_dir = os.path.join(settings.OUTPUT_DIR, f"hearing_{hearing_id}")
            os.makedirs(output_dir, exist_ok=True)

            aligned_paths = []
            for aligned in alignment_result['aligned_audios']:
                aligned_path = self.aligner.save_aligned_audio(aligned, output_dir)
                aligned_paths.append({
                    'microphone_id': aligned.microphone_id,
                    'aligned_path': aligned_path,
                    'offset': aligned.offset
                })

                rec = next(r for r in recordings if r.microphone_id == aligned.microphone_id)
                audio, sr = self.aligner.load_audio(aligned_path)
                rec.duration = len(audio) / sr
                rec.sample_rate = sr
                rec.noise_level = estimate_noise_level(audio, sr)
                rec.status = "aligned"

            db.commit()

            transcription_results = []
            for aligned_info in aligned_paths:
                trans_result = self.transcriber.transcribe(aligned_info['aligned_path'])
                transcription_results.append({
                    'microphone_id': aligned_info['microphone_id'],
                    'transcription': trans_result,
                    'offset': aligned_info['offset']
                })

            synchronized_segments = self.aligner.compute_synchronized_transcript(
                [
                    {
                        'microphone_id': tr['microphone_id'],
                        'segments': [
                            {
                                'start_time': seg.start_time,
                                'end_time': seg.end_time,
                                'text': seg.text
                            }
                            for seg in tr['transcription'].segments
                        ]
                    }
                    for tr in transcription_results
                ],
                {tr['microphone_id']: tr['offset'] for tr in transcription_results}
            )

            for tr in transcription_results:
                rec = next(r for r in recordings if r.microphone_id == tr['microphone_id'])

                diarization_result = self.diarizer.diarize(
                    aligned_info['aligned_path'],
                    num_speakers=2
                )

                diarization_result = self.diarizer.classify_speaker_roles(
                    diarization_result,
                    tr['transcription'].full_text
                )

                for turn in diarization_result.speaker_turns:
                    speaker_seg = SpeakerSegment(
                        recording_id=rec.id,
                        speaker_id=turn.speaker_id,
                        speaker_role=turn.speaker_role,
                        start_time=turn.start_time + tr['offset'],
                        end_time=turn.end_time + tr['offset'],
                        confidence=turn.confidence
                    )
                    db.add(speaker_seg)

                transcription = Transcription(
                    recording_id=rec.id,
                    full_text=tr['transcription'].full_text,
                    language=tr['transcription'].language
                )
                db.add(transcription)
                db.flush()

                for seg in tr['transcription'].segments:
                    trans_seg = TranscriptionSegment(
                        transcription_id=transcription.id,
                        start_time=seg.start_time + tr['offset'],
                        end_time=seg.end_time + tr['offset'],
                        text=seg.text
                    )
                    db.add(trans_seg)

                rec.status = "transcribed"

            db.commit()

            merged_transcript = self._merge_all_transcripts(recordings, db)

            for rec in recordings:
                rec.status = "completed"
            db.commit()

            return {
                'hearing_id': hearing_id,
                'reference_microphone_id': alignment_result['reference_microphone_id'],
                'time_offsets': alignment_result['time_offsets'],
                'merged_transcript': merged_transcript,
                'aligned_files_count': len(aligned_paths)
            }

        except Exception as e:
            for rec in recordings:
                rec.status = "failed"
            db.commit()
            raise e
        finally:
            db.close()

    def _merge_all_transcripts(
        self,
        recordings: List[Recording],
        db
    ) -> Dict[str, Any]:
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
                    speaker_info = self._get_speaker_for_segment(
                        seg.start_time,
                        seg.end_time,
                        speaker_segments
                    )
                    all_segments.append({
                        'start_time': seg.start_time,
                        'end_time': seg.end_time,
                        'text': seg.text,
                        'speaker_id': speaker_info.get('speaker_id'),
                        'speaker_role': speaker_info.get('speaker_role'),
                        'microphone_id': rec.microphone_id,
                        'location': rec.location_name
                    })

        all_segments.sort(key=lambda x: x['start_time'])

        merged_text = ' '.join([seg['text'] for seg in all_segments])

        return {
            'full_text': merged_text,
            'segments': all_segments,
            'total_duration': max(seg['end_time'] for seg in all_segments) if all_segments else 0
        }

    def _get_speaker_for_segment(
        self,
        start_time: float,
        end_time: float,
        speaker_segments: List[SpeakerSegment]
    ) -> Dict[str, Optional[str]]:
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
