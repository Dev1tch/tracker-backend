from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.notes import NotesDocument, NotesUpdate
from app.schemas.user import User
from app.services.notes_service import NotesService

router = APIRouter()


@router.get("/", response_model=NotesDocument, status_code=status.HTTP_200_OK)
def get_notes_document(
    current_user: User = Depends(get_current_user),
    notes_service: NotesService = Depends(ServiceProvider.get_notes_service),
):
    return notes_service.get_or_create(current_user.id)


@router.put("/", status_code=status.HTTP_200_OK)
def update_notes_document(
    payload: NotesUpdate,
    current_user: User = Depends(get_current_user),
    notes_service: NotesService = Depends(ServiceProvider.get_notes_service),
):
    outcome, document = notes_service.update(
        current_user.id, payload.tree, payload.base_version
    )
    if outcome == "conflict":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "conflict",
                "detail": "Document version is out of date.",
                "document": _serialize(document),
            },
        )
    if not document:
        raise HTTPException(status_code=500, detail="Failed to persist notes document.")
    return _serialize(document)


def _serialize(document: dict) -> dict:
    return {
        "user_id": str(document.get("user_id")),
        "tree": document.get("tree"),
        "version": int(document.get("version", 0)),
        "updated_at": document.get("updated_at"),
    }
