from typing import List
from fastapi import APIRouter
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from poster_gen import generate_poster_pic2pic, generate_poster_text2pic, get_poster

router = APIRouter(prefix="/api/poster", tags=["Poster"])


class PosterTaskPayload(BaseModel):
    prompt: str = Field(..., description="用户输入的文本")
    references: List[str] = Field(default_factory=list)
    base_images: List[str] = Field(default_factory=list)
    gen_num: int = 2


@router.post("/tasks")
async def create_poster_task(payload: PosterTaskPayload):
    images: List[str] = payload.references + payload.base_images
    if images:
        return generate_poster_pic2pic(payload.prompt, images, payload.gen_num)
    return generate_poster_text2pic(payload.prompt, payload.gen_num)


@router.get("/tasks/{task_id}")
async def fetch_poster_task(task_id: str):
    return get_poster(task_id)
