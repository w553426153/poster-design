"""
Image cutout (background removal) endpoints
"""
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from rembg import remove

from ..config import settings

router = APIRouter()


def _build_public_url(relative_path: str) -> str:
    cleaned = relative_path.replace('\\', '/')
    if not cleaned.startswith('/'):
        cleaned = '/' + cleaned
    return f"/api/files{cleaned}"


@router.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    try:
        processed = remove(data)
    except Exception as exc:  # pragma: no cover - rembg internal errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Background removal failed: {exc}") from exc

    target_dir = Path("cutout") / datetime.utcnow().strftime("%Y/%m/%d")
    filename = f"{uuid4().hex}.png"
    relative_path = target_dir / filename
    output_path = Path(settings.UPLOAD_FOLDER) / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_bytes(processed)

    public_path = str(relative_path).replace('\\', '/')

    return {
        "status": "success",
        "file_path": public_path,
        "url": _build_public_url(public_path),
    }
