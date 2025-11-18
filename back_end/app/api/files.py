"""
File operations API endpoints
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import os
import shutil
from datetime import datetime
from pydantic import BaseModel
import importlib.util

OssUploader = None
oss_path = Path(__file__).resolve().parents[1].parent / 'oss.py'
if oss_path.exists():
  spec = importlib.util.spec_from_file_location('oss', oss_path)
  if spec and spec.loader:
    oss_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oss_module)
    OssUploader = getattr(oss_module, 'Upload', None)

from ..config import settings

router = APIRouter()

class OssUploadRequest(BaseModel):
    file_path: str
    remote_path: str | None = None

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server
    
    - **file**: The file to upload
    """
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_FOLDER)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a unique filename to prevent collisions
        file_ext = Path(file.filename).suffix if file.filename else ''
        file_name = f"{os.urandom(16).hex()}{file_ext}"
        file_path = upload_dir / file_name
        
        # Save the file
        with file_path.open('wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "status": "success",
            "file_path": file_name,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """
    Get a file from the server
    
    - **file_path**: Path to the file relative to the uploads directory
    """
    file_full_path = Path(settings.UPLOAD_FOLDER) / file_path
    
    # Security check to prevent directory traversal
    try:
        file_full_path.resolve().relative_to(Path(settings.UPLOAD_FOLDER).resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if not file_full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        file_full_path,
        filename=file_path.split('/')[-1],
        media_type="application/octet-stream"
    )

@router.post("/upload-oss")
async def upload_file_to_oss(payload: OssUploadRequest):
    if OssUploader is None:
        raise HTTPException(status_code=501, detail="OSS uploader not configured")
    upload_dir = Path(settings.UPLOAD_FOLDER)
    local_path = upload_dir / payload.file_path
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    remote_dir = payload.remote_path or f"poster/base/{datetime.utcnow():%Y/%m/%d}"
    uploader = OssUploader()
    oss_url = uploader.upload_file(str(local_path), remote_dir)
    if not oss_url:
        raise HTTPException(status_code=500, detail="OSS upload failed")
    return {
        "status": "success",
        "oss_url": oss_url,
        "remote_path": remote_dir,
    }
