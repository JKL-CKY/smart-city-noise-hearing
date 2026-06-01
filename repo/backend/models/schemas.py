from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any


class RecordingBase(BaseModel):
    microphone_id: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    recorded_at: datetime
    duration: Optional[float] = None
    noise_level: Optional[float] = None


class RecordingCreate(RecordingBase):
    filename: str
    file_path: str


class RecordingResponse(RecordingBase):
    id: int
    filename: str
    status: str
    created_at: datetime
    hearing_id: Optional[int] = None

    class Config:
        from_attributes = True


class HearingBase(BaseModel):
    title: str
    description: Optional[str] = None
    district: Optional[str] = None
    scheduled_at: datetime


class HearingCreate(HearingBase):
    pass


class HearingResponse(HearingBase):
    id: int
    status: str
    created_at: datetime
    recordings: List[RecordingResponse] = []

    class Config:
        from_attributes = True


class TranscriptionSegmentResponse(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str
    speaker_id: Optional[str] = None

    class Config:
        from_attributes = True


class TranscriptionResponse(BaseModel):
    id: int
    recording_id: int
    full_text: str
    language: Optional[str] = None
    segments: List[TranscriptionSegmentResponse] = []

    class Config:
        from_attributes = True


class SpeakerSegmentResponse(BaseModel):
    id: int
    speaker_id: str
    speaker_role: Optional[str] = None
    start_time: float
    end_time: float
    confidence: float

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    summary: str
    key_points: List[str]
    zoning_recommendations: List[Dict[str, Any]]
    noise_level_analysis: Dict[str, Any]


class ReportCreate(ReportBase):
    hearing_id: int
    full_markdown: str


class ReportResponse(ReportBase):
    id: int
    hearing_id: int
    full_markdown: str
    sent_to_env_dept: bool
    sent_to_planning: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NoiseReportPointBase(BaseModel):
    title: str
    description: Optional[str] = None
    latitude: float
    longitude: float
    noise_level: Optional[float] = None
    reporter_name: Optional[str] = None
    reporter_contact: Optional[str] = None


class NoiseReportPointCreate(NoiseReportPointBase):
    pass


class NoiseReportPointResponse(NoiseReportPointBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MicrophoneDeviceBase(BaseModel):
    device_id: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None


class MicrophoneDeviceResponse(MicrophoneDeviceBase):
    id: int
    is_active: bool
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessingStatusResponse(BaseModel):
    recording_id: int
    status: str
    stage: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None


class AlignmentResult(BaseModel):
    reference_id: str
    aligned_files: List[Dict[str, Any]]
    time_offsets: Dict[str, float]
