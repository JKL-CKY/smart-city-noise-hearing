import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np
from config import settings


@dataclass
class SpeakerTurn:
    speaker_id: str
    speaker_role: Optional[str]
    start_time: float
    end_time: float
    confidence: float


@dataclass
class DiarizationResult:
    speaker_turns: List[SpeakerTurn]
    unique_speakers: List[str]
    processing_time: float


class PyannoteDiarizer:
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token or settings.PYANNOTE_AUTH_TOKEN
        self._pipeline = None
        self._embedding_model = None

    @property
    def pipeline(self):
        if self._pipeline is None:
            if not self.auth_token:
                raise ValueError("Pyannote auth token is required")
            from pyannote.audio import Pipeline
            self._pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.auth_token
            )
        return self._pipeline

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            if not self.auth_token:
                raise ValueError("Pyannote auth token is required")
            from pyannote.audio import Inference
            self._embedding_model = Inference(
                "pyannote/embedding",
                use_auth_token=self.auth_token
            )
        return self._embedding_model

    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        import time
        start_time = time.time()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        diarization = self.pipeline(
            audio_path,
            num_speakers=num_speakers
        )

        speaker_turns = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_turns.append(SpeakerTurn(
                speaker_id=speaker,
                speaker_role=None,
                start_time=float(turn.start),
                end_time=float(turn.end),
                confidence=1.0
            ))

        unique_speakers = list(set([turn.speaker_id for turn in speaker_turns]))
        processing_time = time.time() - start_time

        return DiarizationResult(
            speaker_turns=speaker_turns,
            unique_speakers=unique_speakers,
            processing_time=processing_time
        )

    def classify_speaker_roles(
        self,
        diarization_result: DiarizationResult,
        transcription_text: str
    ) -> DiarizationResult:
        """
        Classify speakers into 'complainant' or 'official' based on speaking patterns
        and transcription content analysis.
        """
        speaker_stats = {}
        for turn in diarization_result.speaker_turns:
            if turn.speaker_id not in speaker_stats:
                speaker_stats[turn.speaker_id] = {
                    'total_duration': 0.0,
                    'num_turns': 0,
                    'avg_duration': 0.0
                }
            duration = turn.end_time - turn.start_time
            speaker_stats[turn.speaker_id]['total_duration'] += duration
            speaker_stats[turn.speaker_id]['num_turns'] += 1

        for speaker_id, stats in speaker_stats.items():
            stats['avg_duration'] = stats['total_duration'] / stats['num_turns'] if stats['num_turns'] > 0 else 0

        complainant_keywords = ['噪音', '噪声', '投诉', '扰民', '影响', '休息', '睡眠', '晚上', '深夜',
                               '请求', '要求', '解决', '问题', '严重', '无法忍受']

        official_keywords = ['您好', '请讲', '请问', '了解', '明白', '记录', '处理', '反馈',
                             '规定', '条例', '管理', '协调', '建议', '方案']

        speaker_keyword_counts = {}
        for turn in diarization_result.speaker_turns:
            speaker_id = turn.speaker_id
            if speaker_id not in speaker_keyword_counts:
                speaker_keyword_counts[speaker_id] = {'complainant': 0, 'official': 0}

        text_lower = transcription_text.lower()
        for speaker_id in speaker_keyword_counts:
            for keyword in complainant_keywords:
                if keyword in transcription_text:
                    speaker_keyword_counts[speaker_id]['complainant'] += 1
            for keyword in official_keywords:
                if keyword in transcription_text:
                    speaker_keyword_counts[speaker_id]['official'] += 1

        speakers = list(speaker_stats.keys())
        if len(speakers) >= 2:
            speakers_sorted_by_duration = sorted(
                speakers,
                key=lambda s: speaker_stats[s]['total_duration'],
                reverse=True
            )

            for i, speaker_id in enumerate(speakers_sorted_by_duration):
                counts = speaker_keyword_counts[speaker_id]
                if counts['complainant'] > counts['official']:
                    role = 'complainant'
                elif counts['official'] > counts['complainant']:
                    role = 'official'
                else:
                    role = 'complainant' if i == 0 else 'official'

                for turn in diarization_result.speaker_turns:
                    if turn.speaker_id == speaker_id:
                        turn.speaker_role = role
        else:
            for turn in diarization_result.speaker_turns:
                turn.speaker_role = 'unknown'

        return diarization_result

    def merge_transcription_with_diarization(
        self,
        transcription_segments: List[Dict[str, Any]],
        diarization_result: DiarizationResult
    ) -> List[Dict[str, Any]]:
        merged_segments = []

        for trans_seg in transcription_segments:
            trans_start = trans_seg['start_time']
            trans_end = trans_seg['end_time']

            overlapping_speakers = []
            for speaker_turn in diarization_result.speaker_turns:
                overlap_start = max(trans_start, speaker_turn.start_time)
                overlap_end = min(trans_end, speaker_turn.end_time)
                overlap_duration = overlap_end - overlap_start

                if overlap_duration > 0:
                    overlapping_speakers.append({
                        'speaker_id': speaker_turn.speaker_id,
                        'speaker_role': speaker_turn.speaker_role,
                        'overlap': overlap_duration
                    })

            if overlapping_speakers:
                best_speaker = max(overlapping_speakers, key=lambda x: x['overlap'])
                speaker_id = best_speaker['speaker_id']
                speaker_role = best_speaker['speaker_role']
            else:
                speaker_id = None
                speaker_role = None

            merged_segments.append({
                **trans_seg,
                'speaker_id': speaker_id,
                'speaker_role': speaker_role
            })

        return merged_segments
