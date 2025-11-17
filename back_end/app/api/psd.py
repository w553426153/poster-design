"""
PSD Processing API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import os

from ..config import settings
from ..services.psd_service import PSDService

router = APIRouter()
psd_service = PSDService()

@router.post("/process")
async def process_psd(
    file: UploadFile = File(...),
    skip_ocr: bool = Form(False),
    output_format: str = Form('png'),
    return_canvas: bool = Form(False),
    canvas_mode: str = Form('leaf'),
):
    """
    Process a PSD file by removing text layers and optionally checking for text in images
    
    - **file**: The PSD file to process
    - **skip_ocr**: Whether to skip OCR check for text in images (faster but less accurate)
    - **output_format**: Output format (png, jpg, etc.)
    """
    # Check file extension
    if not file.filename.lower().endswith(('.psd', '.psb')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PSD files are supported"
        )
    
    # Process the file
    # canvas_mode: 'leaf' 按照 process_psd_layers.py 的导出逻辑（底层图层作为元素）
    #              'group' 顶层分组作为元素
    if canvas_mode not in ('leaf', 'group'):
        canvas_mode = 'leaf'

    result = await psd_service.process_psd(file, skip_ocr, output_format, return_canvas, canvas_mode)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result

@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download a processed file
    
    - **file_path**: Relative path to the file in the uploads directory
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
