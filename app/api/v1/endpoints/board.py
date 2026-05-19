from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.board import BoardDocument, BoardUpdate
from app.schemas.user import User
from app.services.board_service import BoardService

router = APIRouter()


@router.get("/", response_model=BoardDocument, status_code=status.HTTP_200_OK)
def get_board_document(
    current_user: User = Depends(get_current_user),
    board_service: BoardService = Depends(ServiceProvider.get_board_service),
):
    return board_service.get_or_create(current_user.id)


@router.put("/", status_code=status.HTTP_200_OK)
def update_board_document(
    payload: BoardUpdate,
    current_user: User = Depends(get_current_user),
    board_service: BoardService = Depends(ServiceProvider.get_board_service),
):
    outcome, document = board_service.update(
        current_user.id, payload.state, payload.base_version
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
        raise HTTPException(status_code=500, detail="Failed to persist board document.")
    return _serialize(document)


def _serialize(document: dict) -> dict:
    return {
        "user_id": str(document.get("user_id")),
        "state": document.get("state"),
        "version": int(document.get("version", 0)),
        "updated_at": document.get("updated_at"),
    }
