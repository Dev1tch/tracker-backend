from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.board import BoardDocument, BoardUpdate
from app.schemas.user import User
from app.services.board_service import (
    BoardService,
    BoardUnsafeOverwriteError,
    BoardUnversionedUpdateError,
    BoardVersionConflictError,
)

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
    try:
        document = board_service.update(
            current_user.id,
            payload.state,
            base_version=payload.base_version,
            allow_empty_overwrite=payload.allow_empty_overwrite,
        )
    except BoardVersionConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Board was updated elsewhere. Refresh before saving.",
        )
    except BoardUnsafeOverwriteError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Refusing to replace a non-empty board with an unversioned empty board.",
        )
    except BoardUnversionedUpdateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Board save must include the version it is based on.",
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
