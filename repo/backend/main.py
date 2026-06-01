from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import recordings, hearings, noise_map, reports
from models.database import engine, Base
from config import settings
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Smart City Noise Hearing System",
    description="分布式麦克风网络的智慧城市噪声听证会纪要系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recordings.router, prefix="/api/recordings", tags=["录音管理"])
app.include_router(hearings.router, prefix="/api/hearings", tags=["听证会管理"])
app.include_router(noise_map.router, prefix="/api/noise-map", tags=["噪声地图"])
app.include_router(reports.router, prefix="/api/reports", tags=["报告管理"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "噪声听证会系统运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
