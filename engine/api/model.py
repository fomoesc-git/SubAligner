"""Model management API endpoints"""
import torch
import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from models.model_manager import ModelManager

router = APIRouter()
model_manager = ModelManager()


class ModelStatusResponse(BaseModel):
    model_ready: bool
    gpu_available: bool
    gpu_name: str = ""
    model_path: str = ""
    model_name: str = ""


@router.post("/model/status", response_model=ModelStatusResponse)
async def model_status():
    """Get model and GPU status"""
    gpu_available = torch.cuda.is_available()
    gpu_name = ""
    if gpu_available:
        gpu_name = torch.cuda.get_device_name(0)
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        gpu_available = True
        gpu_name = "Apple Silicon (MPS)"

    model_ready = model_manager.is_model_ready()

    return ModelStatusResponse(
        model_ready=model_ready,
        gpu_available=gpu_available,
        gpu_name=gpu_name,
        model_path=str(model_manager.model_dir) if model_ready else "",
        model_name="wav2vec2-base-960h" if model_ready else "",
    )


class DownloadRequest(BaseModel):
    pass


class DownloadResponse(BaseModel):
    task_id: str
    message: str


@router.post("/model/download", response_model=DownloadResponse)
async def download_model():
    """Download the alignment model (blocking download in thread pool)"""
    try:
        await asyncio.to_thread(model_manager.download_model)
        return DownloadResponse(task_id="1", message="Model downloaded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model download failed: {str(e)}")
