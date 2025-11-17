"""
File operations API endpoints
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

import mimetypes
import os
import shutil
import ssl
import urllib.parse

from fastapi import APIRouter, HTTPException, Response, UploadFile, File, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..config import settings

try:
    from oss import Upload
    _oss_import_error: Optional[Exception] = None
except Exception as exc:  # pragma: no cover - optional dependency
    Upload = None  # type: ignore
    _oss_import_error = exc

router = APIRouter()


class OssUploadRequest(BaseModel):
    file_path: str
    remote_path: Optional[str] = None

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
    # Decode URL encoded file path
    decoded_file_path = urllib.parse.unquote(file_path)
    file_full_path = Path(settings.UPLOAD_FOLDER) / decoded_file_path
    
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
    
    # Determine the media type based on file extension
    media_type, _ = mimetypes.guess_type(file_full_path)
    if not media_type:
        media_type = "application/octet-stream"
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return FileResponse(
        file_full_path,
        filename=decoded_file_path.split('/')[-1],
        media_type=media_type,
        headers=headers,
    )


@router.get("/proxy")
async def proxy_image(url: str):
    """Development helper to fetch third-party images bypassing invalid certs/CORS."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL scheme")
    try:
        context = ssl._create_unverified_context() if parsed.scheme == "https" else None
        req = Request(url, headers={"User-Agent": "PosterDesign/1.0"})
        with urlopen(req, context=context) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type") or "application/octet-stream"
            return Response(
                content=data,
                media_type=ctype,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                },
            )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Proxy fetch failed: {e}")


@router.post("/upload-oss")
async def upload_file_to_oss(payload: OssUploadRequest):
    """Push an already-uploaded local file to OSS and return its remote URL."""
    if Upload is None:
        detail = "OSS uploader unavailable"
        if _oss_import_error:
            detail = f"{detail}: {_oss_import_error}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

    upload_root = Path(settings.UPLOAD_FOLDER).resolve()
    target_path = (upload_root / payload.file_path).resolve()
    try:
        target_path.relative_to(upload_root)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not target_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    remote_dir = payload.remote_path or f"poster/base/{datetime.utcnow():%Y/%m/%d}"
    uploader = Upload()
    oss_url = uploader.upload_file(str(target_path), remote_dir)
    if not oss_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OSS upload failed")
    return {
        "status": "success",
        "oss_url": oss_url,
        "remote_path": remote_dir,
        "file_path": payload.file_path,
    }
