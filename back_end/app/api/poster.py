from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from pathlib import Path
import importlib.util
import requests
import uuid
from datetime import datetime
from rembg import remove

from poster_gen import generate_poster_pic2pic, generate_poster_text2pic, get_poster
from ..config import settings

router = APIRouter(prefix="/api/poster", tags=["Poster"])


class PosterTaskPayload(BaseModel):
    prompt: str = Field(..., description="用户输入的文本")
    references: List[str] = Field(default_factory=list)
    base_images: List[str] = Field(default_factory=list)
    gen_num: int = 2
    width: Optional[int] = None
    height: Optional[int] = None
    mode: Optional[str] = None


def _load_oss_uploader():
    oss_path = Path(__file__).resolve().parents[2] / 'oss.py'
    if not oss_path.exists():
        return None
    spec = importlib.util.spec_from_file_location('oss', oss_path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, 'Upload', None)


def _process_art_images(urls: List[str]) -> List[str]:
    if not urls:
        return urls
    uploader_cls = _load_oss_uploader()
    if uploader_cls is None:
        return urls
    upload_dir = Path(settings.UPLOAD_FOLDER)
    temp_dir = upload_dir / 'art_tmp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    processed: List[str] = []
    uploader = uploader_cls()
    for url in urls:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            output_bytes = remove(resp.content)
            file_name = f"art_{uuid.uuid4().hex}.png"
            temp_path = temp_dir / file_name
            with temp_path.open('wb') as f:
                f.write(output_bytes)
            remote_dir = f"poster/art/{datetime.utcnow():%Y/%m/%d}"
            oss_url = uploader.upload_file(str(temp_path), remote_dir)
            if oss_url:
                processed.append(oss_url)
            else:
                processed.append(url)
            temp_path.unlink(missing_ok=True)
        except Exception:
            processed.append(url)
    return processed


@router.post("/tasks")
async def create_poster_task(payload: PosterTaskPayload):
    images: List[str] = payload.references + payload.base_images
    if images:
        result = generate_poster_pic2pic(payload.prompt, images, payload.gen_num)
    else:
        result = generate_poster_text2pic(payload.prompt, payload.gen_num, payload.width, payload.height)
    if payload.mode == 'art' and result.get('code') == 0:
        data = result.get('data') or {}
        urls = data.get('image_urls') or []
        data['image_urls'] = _process_art_images(urls)
        result['data'] = data
    return result


@router.get("/tasks/{task_id}")
async def fetch_poster_task(task_id: str):
    return get_poster(task_id)
