import uuid
import aiofiles
import os
import magic
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.core.config import settings
from app.api import deps

router = APIRouter()
ALLOWED_MIME_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp"
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user: deps.CurrentUser = Depends(deps.get_current_user)
):
    # Read first 2048 bytes for magic numbers
    header = await file.read(2048)
    # Reset file pointer to beginning so the entire file is saved later
    await file.seek(0)

    mime_type = magic.from_buffer(header, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_MIME_TYPES.values())}"
        )

    ext = ALLOWED_MIME_TYPES[mime_type]
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    total_bytes = 0
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                total_bytes += len(content)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB."
                    )
                await out_file.write(content)
    except HTTPException:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
        
    url = f"/static/{unique_filename}"
    return {"url": url}