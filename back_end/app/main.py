from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api import psd, files, templates, materials, poster, cutout

app = FastAPI(
    title="Poster Design API",
    description="API for processing PSD files in the Poster Design application",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(psd.router, prefix="/api/psd", tags=["PSD Processing"])
app.include_router(files.router, prefix="/api/files", tags=["File Operations"])
app.include_router(materials.router, prefix="/api", tags=["Materials"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])
app.include_router(poster.router, tags=["Poster"])
app.include_router(cutout.router, prefix="/api/cutout", tags=["Cutout"])

@app.get("/")
async def root():
    return {"message": "Welcome to Poster Design API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
