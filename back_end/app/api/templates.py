from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import uuid

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_FILE = DATA_DIR / "templates.json"

def _load_store() -> Dict[str, Any]:
    if TEMPLATE_FILE.exists():
        with TEMPLATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"templates": []}

def _save_store(data: Dict[str, Any]) -> None:
    with TEMPLATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class TemplatePayload(BaseModel):
    id: Optional[str] = None
    title: str = Field(default="未命名模板")
    data: str
    width: int
    height: int
    cover: Optional[str] = None
    state: int = 1
    category: int = 1

router = APIRouter()

def _build_list_item(tpl: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": tpl["id"],
        "title": tpl["title"],
        "width": tpl["width"],
        "height": tpl["height"],
        "cover": tpl.get("cover", ""),
        "state": tpl.get("state", 1),
        "isDelect": False,
        "fail": False,
        "top": 0,
        "left": 0,
        "data": tpl.get("data"),
    }

@router.get("/design/list")
async def list_templates(page: int = 1, pageSize: int = 20, cate: Optional[int] = None, search: str = ""):
    store = _load_store()
    templates = store.get("templates", [])
    if search:
        templates = [tpl for tpl in templates if search.lower() in tpl.get("title", "").lower()]
    total = len(templates)
    start = (page - 1) * pageSize
    end = start + pageSize
    sliced = templates[start:end]
    list_data = [_build_list_item(tpl) for tpl in sliced]
    return {"code": 200, "result": {"list": list_data, "total": total}}

@router.get("/design/temp")
async def get_template(id: str):
    store = _load_store()
    for tpl in store.get("templates", []):
        if str(tpl["id"]) == str(id):
            return {"stat": 1, "data": tpl}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

@router.post("/design/edit")
async def edit_template(payload: TemplatePayload):
    store = _load_store()
    templates = store.setdefault("templates", [])
    now = datetime.utcnow().isoformat()
    if payload.id:
        for tpl in templates:
            if str(tpl["id"]) == str(payload.id):
                tpl.update(payload.dict(exclude_none=True))
                tpl["updated_at"] = now
                _save_store(store)
                return {"stat": 1, "id": tpl["id"]}
    new_id = payload.id or str(uuid.uuid4())
    new_tpl = payload.dict()
    new_tpl["id"] = new_id
    new_tpl["created_at"] = now
    new_tpl["updated_at"] = now
    templates.insert(0, new_tpl)
    _save_store(store)
    return {"stat": 1, "id": new_id}
