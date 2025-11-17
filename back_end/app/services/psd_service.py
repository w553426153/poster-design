"""
PSD processing service
"""
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import UploadFile

from ..config import settings
from ..utils.psd_utils import PSDProcessor

class PSDService:
    def __init__(self):
        self.psd_processor = PSDProcessor(tesseract_cmd=settings.TESSERACT_CMD)
        self.upload_dir = Path(settings.UPLOAD_FOLDER)
        
    async def save_upload_file(self, file: UploadFile) -> Path:
        """Save uploaded file to the uploads directory"""
        # Create a unique filename to prevent collisions
        file_ext = Path(file.filename).suffix if file.filename else '.psd'
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = self.upload_dir / file_name
        
        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with file_path.open('wb') as buffer:
            content = await file.read()
            buffer.write(content)
            
        return file_path
    
    async def process_psd(
        self, 
        file: UploadFile, 
        skip_ocr: bool = False,
        output_format: str = 'png',
        return_canvas: bool = False,
        canvas_mode: str = 'leaf',
    ) -> Dict[str, Any]:
        """
        Process a PSD file by removing text layers and optionally checking for text in images
        """
        try:
            # Save the uploaded file
            input_path = await self.save_upload_file(file)
            
            # Create output path
            output_filename = f"{input_path.stem}_processed.{output_format}"
            output_path = self.upload_dir / output_filename
            
            # Process the PSD
            result = self.psd_processor.process_psd(
                input_path=str(input_path), 
                output_path=str(output_path),
                skip_ocr=skip_ocr,
                return_canvas=return_canvas,
                assets_root=str(self.upload_dir),
                canvas_mode=canvas_mode,
            )
            
            # Clean up the input file
            if input_path.exists():
                input_path.unlink()
                
            # If processing failed, return the error
            if result["status"] == "error":
                return result
                
            # Return the relative path for the client to download
            relative_path = str(output_path.relative_to(self.upload_dir))
            
            ret: Dict[str, Any] = {
                "status": "success",
                "file_path": relative_path,
                "message": "PSD processed successfully",
            }
            if return_canvas and result.get("canvas"):
                ret["canvas"] = result["canvas"]
            return ret
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to process PSD: {str(e)}"
            }
