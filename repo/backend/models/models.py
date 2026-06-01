from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    microphone_id = Column(String(100), nullable=False)
    location_name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    recorded_at = Column(DateTime, nullable=False)
    duration = Column(Float)
    sample_rate = Column(Integer)
    noise_level = Column(Float)
    status = Column(String(50), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)

    hearing_id = Column(Integer, ForeignKey("hearings.id"), nullable=True)
    hearing = relationship("Hearing", back_populates="recordings")

    transcription = relationship("Transcription", back_populates="recording", uselist=False)
    speaker_segments = relationship("SpeakerSegment", back_populates="recording")


class Hearing(Base):
    __tablename__ = "hearings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    district = Column(String(100))
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    recordings = relationship("Recording", back_populates="hearing")
    report = relationship("Report", back_populates="hearing", uselist=False)


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    full_text = Column(Text)
    language = Column(String(50))
    processed_at = Column(DateTime, default=datetime.utcnow)

    recording = relationship("Recording", back_populates="transcription")
    segments = relationship("TranscriptionSegment", back_populates="transcription")


class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"

    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), nullable=False)
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(Text)
    speaker_id = Column(String(100))

    transcription = relationship("Transcription", back_populates="segments")


class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("recordings.id"), nullable=False)
    speaker_id = Column(String(100), nullable=False)
    speaker_role = Column(String(50))
    start_time = Column(Float)
    end_time = Column(Float)
    confidence = Column(Float)

    recording = relationship("Recording", back_populates="speaker_segments")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    hearing_id = Column(Integer, ForeignKey("hearings.id"), nullable=False)
    summary = Column(Text)
    key_points = Column(JSON)
    zoning_recommendations = Column(JSON)
    noise_level_analysis = Column(JSON)
    full_markdown = Column(Text)
    sent_to_env_dept = Column(Boolean, default=False)
    sent_to_planning = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    hearing = relationship("Hearing", back_populates="report")


class NoiseReportPoint(Base):
    __tablename__ = "noise_report_points"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    noise_level = Column(Float)
    reporter_name = Column(String(100))
    reporter_contact = Column(String(200))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class MicrophoneDevice(Base):
    __tablename__ = "microphone_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False)
    location_name = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    district = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime)
