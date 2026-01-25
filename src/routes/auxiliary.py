from fastapi.responses import FileResponse
from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    file_path = STATIC_DIR / "favicon.ico"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Favicon.ico not found")
    return FileResponse(file_path)


@router.get("/robots.txt", include_in_schema=False)
async def robots():
    file_path = STATIC_DIR / "robots.txt"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Robots.txt not found")
    return FileResponse(file_path)


@router.get("/", response_class=FileResponse)
async def root():
    file_path = STATIC_DIR / "root.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(file_path)
