from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.media import MediaObject
from app.schemas.user import User
from app.services.media_service import MediaService

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIMES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}


@router.post("/", response_model=MediaObject, status_code=status.HTTP_201_CREATED)
async def upload_media(
    kind: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(ServiceProvider.get_media_service),
):
    if kind not in ("notes", "board"):
        raise HTTPException(status_code=400, detail="kind must be 'notes' or 'board'")

    mime = file.content_type or ""
    if mime and mime not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {mime}")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        record = media_service.upload(
            user_id=current_user.id,
            kind=kind,
            file_bytes=contents,
            mime=mime or None,
            filename=file.filename,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Upload failed: {err}")

    return record
