from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from models import (
    get_db, Recording, Hearing, NoiseReportPoint,
    NoiseReportPointResponse, NoiseReportPointCreate,
    MicrophoneDevice, MicrophoneDeviceResponse
)

router = APIRouter()


@router.get("/heatmap")
async def get_noise_heatmap(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=7)
    if not end_time:
        end_time = datetime.utcnow()

    recordings = db.query(Recording).filter(
        Recording.recorded_at >= start_time,
        Recording.recorded_at <= end_time,
        Recording.latitude.isnot(None),
        Recording.longitude.isnot(None)
    ).all()

    heatmap_data = []
    for rec in recordings:
        if rec.noise_level:
            heatmap_data.append({
                'latitude': rec.latitude,
                'longitude': rec.longitude,
                'noise_level': rec.noise_level,
                'location_name': rec.location_name,
                'recorded_at': rec.recorded_at.isoformat(),
                'microphone_id': rec.microphone_id
            })

    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'data_points': len(heatmap_data),
        'heatmap_data': heatmap_data
    }


@router.get("/devices", response_model=List[MicrophoneDeviceResponse])
async def list_microphone_devices(
    is_active: Optional[bool] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MicrophoneDevice)

    if is_active is not None:
        query = query.filter(MicrophoneDevice.is_active == is_active)
    if district:
        query = query.filter(MicrophoneDevice.district == district)

    devices = query.all()
    return devices


@router.post("/devices", response_model=MicrophoneDeviceResponse)
async def create_microphone_device(
    device: MicrophoneDeviceResponse,
    db: Session = Depends(get_db)
):
    db_device = MicrophoneDevice(
        device_id=device.device_id,
        location_name=device.location_name,
        latitude=device.latitude,
        longitude=device.longitude,
        district=device.district,
        is_active=True
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@router.get("/report-points", response_model=List[NoiseReportPointResponse])
async def list_noise_report_points(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(NoiseReportPoint)

    if status:
        query = query.filter(NoiseReportPoint.status == status)

    points = query.order_by(NoiseReportPoint.created_at.desc()).offset(skip).limit(limit).all()
    return points


@router.post("/report-points", response_model=NoiseReportPointResponse)
async def create_noise_report_point(
    point: NoiseReportPointCreate,
    db: Session = Depends(get_db)
):
    db_point = NoiseReportPoint(**point.model_dump())
    db.add(db_point)
    db.commit()
    db.refresh(db_point)
    return db_point


@router.get("/report-points/{point_id}", response_model=NoiseReportPointResponse)
async def get_noise_report_point(point_id: int, db: Session = Depends(get_db)):
    point = db.query(NoiseReportPoint).filter(NoiseReportPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Report point not found")
    return point


@router.put("/report-points/{point_id}/status")
async def update_report_point_status(
    point_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db)
):
    point = db.query(NoiseReportPoint).filter(NoiseReportPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Report point not found")

    point.status = status
    db.commit()
    db.refresh(point)

    return {"message": "Status updated", "status": point.status}


@router.get("/district-stats")
async def get_district_noise_stats(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=30)
    if not end_time:
        end_time = datetime.utcnow()

    devices = db.query(MicrophoneDevice).all()
    district_stats = {}

    for device in devices:
        district = device.district or '未知区域'
        if district not in district_stats:
            district_stats[district] = {
                'device_count': 0,
                'recordings_count': 0,
                'avg_noise_level': 0,
                'max_noise_level': 0,
                'report_points': 0
            }
        district_stats[district]['device_count'] += 1

    recordings = db.query(Recording).filter(
        Recording.recorded_at >= start_time,
        Recording.recorded_at <= end_time
    ).all()

    for rec in recordings:
        device = db.query(MicrophoneDevice).filter(
            MicrophoneDevice.device_id == rec.microphone_id
        ).first()
        district = device.district if device else '未知区域'

        if district not in district_stats:
            district_stats[district] = {
                'device_count': 0,
                'recordings_count': 0,
                'avg_noise_level': 0,
                'max_noise_level': 0,
                'report_points': 0
            }

        stats = district_stats[district]
        stats['recordings_count'] += 1
        if rec.noise_level:
            current_avg = stats['avg_noise_level']
            count = stats['recordings_count']
            stats['avg_noise_level'] = ((current_avg * (count - 1)) + rec.noise_level) / count
            stats['max_noise_level'] = max(stats['max_noise_level'], rec.noise_level)

    report_points = db.query(NoiseReportPoint).filter(
        NoiseReportPoint.created_at >= start_time,
        NoiseReportPoint.created_at <= end_time
    ).all()

    for point in report_points:
        for district in district_stats:
            district_stats[district]['report_points'] += 1
            break

    return {
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'district_stats': district_stats
    }
