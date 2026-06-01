import whisper
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from config import settings


@dataclass
class TranscriptionSegment:
    start_time: float
    end_time: float
    text: str
    speaker_id: Optional[str] = None


@dataclass
class TranscriptionResult:
    full_text: str
    language: str
    segments: List[TranscriptionSegment]
    processing_time: float


class WhisperTranscriber:
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.WHISPER_MODEL
        self._model = None

    @property
    def model(self):
        if self._model is None:
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> TranscriptionResult:
        import time
        start_time = time.time()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False,
            word_timestamps=True
        )

        segments = []
        for seg in result.get('segments', []):
            segments.append(TranscriptionSegment(
                start_time=float(seg['start']),
                end_time=float(seg['end']),
                text=seg['text'].strip()
            ))

        processing_time = time.time() - start_time

        return TranscriptionResult(
            full_text=result.get('text', '').strip(),
            language=result.get('language', 'unknown'),
            segments=segments,
            processing_time=processing_time
        )

    def transcribe_batch(
        self,
        audio_paths: List[str],
        language: Optional[str] = None
    ) -> List[TranscriptionResult]:
        results = []
        for path in audio_paths:
            try:
                result = self.transcribe(path, language=language)
                results.append(result)
            except Exception as e:
                results.append(TranscriptionResult(
                    full_text=f"Error transcribing {path}: {str(e)}",
                    language="error",
                    segments=[],
                    processing_time=0.0
                ))
        return results

    def get_word_timestamps(self, audio_path: str) -> List[Dict[str, Any]]:
        result = self.model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False
        )

        words = []
        for segment in result.get('segments', []):
            for word in segment.get('words', []):
                words.append({
                    'word': word['word'],
                    'start': word['start'],
                    'end': word['end'],
                    'probability': word.get('probability', 0.0)
                })

        return words


def merge_aligned_transcripts(
    transcripts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    all_segments = []
    for trans in transcripts:
        for seg in trans.get('segments', []):
            all_segments.append({
                **seg,
                'microphone_id': trans.get('microphone_id')
            })

    all_segments.sort(key=lambda x: x['start_time'])

    merged_segments = []
    current_segment = None
    gap_threshold = 2.0

    for seg in all_segments:
        if current_segment is None:
            current_segment = seg.copy()
        else:
            if seg['start_time'] - current_segment['end_time'] < gap_threshold:
                current_segment['end_time'] = max(current_segment['end_time'], seg['end_time'])
                current_segment['text'] += ' ' + seg['text']
                if 'microphone_id' in current_segment and 'microphone_id' in seg:
                    if not isinstance(current_segment['microphone_id'], list):
                        current_segment['microphone_id'] = [current_segment['microphone_id']]
                    if seg['microphone_id'] not in current_segment['microphone_id']:
                        current_segment['microphone_id'].append(seg['microphone_id'])
            else:
                merged_segments.append(current_segment)
                current_segment = seg.copy()

    if current_segment:
        merged_segments.append(current_segment)

    full_text = ' '.join([seg['text'] for seg in merged_segments])

    return {
        'full_text': full_text,
        'segments': merged_segments
    }
