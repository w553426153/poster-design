from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

_NOW = datetime.utcnow().isoformat()

def _item(idx: int, title: str, url: str, width: int, height: int, category: str, type_: str) -> Dict[str, Any]:
    return {
        "id": idx,
        "title": title,
        "url": url,
        "thumb": url,
        "thumbUrl": url,
        "imgUrl": url,
        "width": width,
        "height": height,
        "category": category,
        "type": type_,
        "model": type_,
        "original": "open-source",
        "state": 1,
        "created_time": _NOW,
        "updated_time": _NOW,
    }

_STICKERS: List[Dict[str, Any]] = [
    _item(100 + i, f"趣味贴纸 {i+1}", f"https://images.unsplash.com/photo-15{i+3}0?auto=format&fit=crop&w=360&q=60", 360, 360, "sticker", "sticker")
    for i in range(12)
]

_SVG: List[Dict[str, Any]] = [
    _item(200 + i, f"几何矢量 {i+1}", f"https://picsum.photos/seed/svg{i}/420/420", 420, 420, "svg", "vector")
    for i in range(15)
]

_MASKS: List[Dict[str, Any]] = []
for i in range(10):
    _MASKS.append(
        _item(
            300 + i,
            f"容器遮罩 {i+1}",
            f"https://picsum.photos/seed/mask{i}/500/600",
            500,
            600,
            "mask-container" if i < 5 else "mask-shape",
            "mask",
        )
    )

_DATASET = {
    "sticker": _STICKERS,
    "svg": _SVG,
    "mask": _MASKS,
    "mask-container": [item for item in _MASKS if item["category"] == "mask-container"],
    "mask-shape": [item for item in _MASKS if item["category"] == "mask-shape"],
}


@router.get("/design/material")
async def get_material_list(cate: str = "sticker", page: int = 1, pageSize: int = 20):
    data = _DATASET.get(cate, _STICKERS)
    total = len(data)
    start = max(page - 1, 0) * pageSize
    end = start + pageSize
    return {
        "code": 200,
        "result": {
            "list": data[start:end],
            "total": total,
        }
    }
