from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from models import get_db, Report, ReportResponse, Hearing
from notifications import EmailNotificationService
from config import settings

router = APIRouter()


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    hearing_id: Optional[int] = None,
    sent_to_env_dept: Optional[bool] = None,
    sent_to_planning: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Report)

    if hearing_id:
        query = query.filter(Report.hearing_id == hearing_id)
    if sent_to_env_dept is not None:
        query = query.filter(Report.sent_to_env_dept == sent_to_env_dept)
    if sent_to_planning is not None:
        query = query.filter(Report.sent_to_planning == sent_to_planning)

    reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report_markdown(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    hearing = db.query(Hearing).filter(Hearing.id == report.hearing_id).first()
    filename = f"hearing_report_{hearing.title.replace(' ', '_')}_{report_id}.md"

    import tempfile
    from fastapi.responses import FileResponse

    temp_path = os.path.join(tempfile.gettempdir(), filename)
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(report.full_markdown)

    return FileResponse(
        temp_path,
        media_type='text/markdown',
        filename=filename
    )


@router.post("/{report_id}/send-email")
async def resend_report_email(
    report_id: int,
    target: str = Query(..., description="Target: 'env_dept', 'planning', or 'both'"),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    hearing = db.query(Hearing).filter(Hearing.id == report.hearing_id).first()

    email_service = EmailNotificationService()
    results = {}

    if target in ['env_dept', 'both']:
        results['env_dept'] = await email_service.send_notification(
            to_email=settings.ENVIRONMENT_DEPARTMENT_EMAIL,
            subject=f"【噪声听证会报告】{hearing.title}",
            message=report.full_markdown[:500] + "...\n\n请查看附件或系统获取完整报告。"
        )
        if results['env_dept']:
            report.sent_to_env_dept = True

    if target in ['planning', 'both']:
        results['planning'] = await email_service.send_notification(
            to_email=settings.URBAN_PLANNING_EMAIL,
            subject=f"【噪声听证会报告】{hearing.title}",
            message=report.full_markdown[:500] + "...\n\n请查看附件或系统获取完整报告。"
        )
        if results['planning']:
            report.sent_to_planning = True

    db.commit()

    return {
        "message": "Email sending completed",
        "results": results
    }


@router.get("/{report_id}/email-status")
async def get_report_email_status(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "report_id": report_id,
        "sent_to_env_dept": report.sent_to_env_dept,
        "sent_to_planning": report.sent_to_planning,
        "created_at": report.created_at.isoformat()
    }
