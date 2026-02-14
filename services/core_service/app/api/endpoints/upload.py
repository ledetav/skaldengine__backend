import uuid
import aiofiles
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings

router = APIRouter()
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def validate_image(filename: str):
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext

@router.post("/", response_model=dict)
async def upload_file(
    file: UploadFile = File(...)
):
    ext = validate_image(file.filename)
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
    url = f"/static/{unique_filename}"
    return {"url": url}