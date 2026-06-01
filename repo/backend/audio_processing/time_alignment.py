import librosa
import numpy as np
import soundfile as sf
from typing import List, Dict, Tuple, Optional
import os
from scipy.signal import correlate
from dataclasses import dataclass


@dataclass
class AlignedAudio:
    file_path: str
    microphone_id: str
    offset: float
    aligned_audio: np.ndarray
    sample_rate: int
    duration: float


class AudioTimeAligner:
    def __init__(self, reference_microphone_id: Optional[str] = None):
        self.reference_microphone_id = reference_microphone_id

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        audio, sr = librosa.load(file_path, sr=None, mono=True)
        return audio, sr

    def extract_features(self, audio: np.ndarray, sr: int) -> np.ndarray:
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        return mfcc

    def compute_time_offset(
        self,
        reference_audio: np.ndarray,
        target_audio: np.ndarray,
        reference_sr: int,
        target_sr: int
    ) -> float:
        if reference_sr != target_sr:
            target_audio = librosa.resample(target_audio, orig_sr=target_sr, target_sr=reference_sr)

        min_len = min(len(reference_audio), len(target_audio))
        ref_segment = reference_audio[:min_len]
        tgt_segment = target_audio[:min_len]

        correlation = correlate(tgt_segment, ref_segment, mode='full')
        max_index = np.argmax(np.abs(correlation))
        offset_samples = max_index - min_len + 1
        offset_seconds = offset_samples / reference_sr

        return offset_seconds

    def align_recordings(
        self,
        recording_paths: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Align multiple audio recordings from different microphones.

        Args:
            recording_paths: List of dicts with 'file_path' and 'microphone_id'

        Returns:
            Dictionary containing alignment results
        """
        loaded_audio = []
        for rec in recording_paths:
            audio, sr = self.load_audio(rec['file_path'])
            loaded_audio.append({
                'microphone_id': rec['microphone_id'],
                'file_path': rec['file_path'],
                'audio': audio,
                'sample_rate': sr,
                'duration': len(audio) / sr
            })

        if not loaded_audio:
            raise ValueError("No recordings provided for alignment")

        if self.reference_microphone_id:
            reference_idx = next(
                (i for i, r in enumerate(loaded_audio) if r['microphone_id'] == self.reference_microphone_id),
                0
            )
        else:
            reference_idx = 0
            self.reference_microphone_id = loaded_audio[0]['microphone_id']

        reference = loaded_audio[reference_idx]
        results = []
        time_offsets = {}

        for i, target in enumerate(loaded_audio):
            if i == reference_idx:
                offset = 0.0
                aligned_audio = target['audio']
            else:
                offset = self.compute_time_offset(
                    reference['audio'],
                    target['audio'],
                    reference['sample_rate'],
                    target['sample_rate']
                )
                aligned_audio = self._shift_audio(target['audio'], offset, target['sample_rate'])

            results.append(AlignedAudio(
                file_path=target['file_path'],
                microphone_id=target['microphone_id'],
                offset=offset,
                aligned_audio=aligned_audio,
                sample_rate=target['sample_rate'],
                duration=len(aligned_audio) / target['sample_rate']
            ))
            time_offsets[target['microphone_id']] = offset

        return {
            'reference_microphone_id': self.reference_microphone_id,
            'aligned_audios': results,
            'time_offsets': time_offsets
        }

    def _shift_audio(self, audio: np.ndarray, offset_seconds: float, sr: int) -> np.ndarray:
        offset_samples = int(offset_seconds * sr)

        if offset_samples > 0:
            shifted = np.concatenate([np.zeros(offset_samples), audio[:-offset_samples]])
        elif offset_samples < 0:
            shifted = np.concatenate([audio[-offset_samples:], np.zeros(-offset_samples)])
        else:
            shifted = audio.copy()

        return shifted

    def save_aligned_audio(self, aligned: AlignedAudio, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(aligned.file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_aligned.wav")
        sf.write(output_path, aligned.aligned_audio, aligned.sample_rate)
        return output_path

    def compute_synchronized_transcript(
        self,
        transcriptions: List[Dict[str, any]],
        time_offsets: Dict[str, float]
    ) -> List[Dict[str, any]]:
        synchronized = []
        for trans in transcriptions:
            mic_id = trans.get('microphone_id')
            offset = time_offsets.get(mic_id, 0.0)
            adjusted_segments = []
            for seg in trans.get('segments', []):
                adjusted_segments.append({
                    'start_time': seg['start_time'] + offset,
                    'end_time': seg['end_time'] + offset,
                    'text': seg['text'],
                    'speaker_id': seg.get('speaker_id'),
                    'microphone_id': mic_id
                })
            synchronized.extend(adjusted_segments)

        synchronized.sort(key=lambda x: x['start_time'])
        return synchronized


def estimate_noise_level(audio: np.ndarray, sr: int) -> float:
    rms = np.sqrt(np.mean(audio ** 2))
    db = 20 * np.log10(rms + 1e-10)
    db_spl = db + 94
    return float(max(0, min(120, db_spl)))
