from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from jose import jwt, JWTError
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.config import settings
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


class BoardBeaconPayload(BaseModel):
    token: str
    state: Any
    base_version: Optional[int] = None


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


@router.post("/beacon", status_code=status.HTTP_204_NO_CONTENT)
def board_beacon(
    payload: BoardBeaconPayload,
    board_service: BoardService = Depends(ServiceProvider.get_board_service),
):
    """Fire-and-forget endpoint for navigator.sendBeacon on page unload.

    sendBeacon cannot set custom headers, so the JWT travels in the body.
    Errors are intentionally swallowed (204 always) — the real PUT path is
    authoritative; this is just a safety net for refresh-during-save.
    """
    try:
        decoded = jwt.decode(
            payload.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    sub = decoded.get("sub")
    if not sub:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    try:
        user_id = UUID(sub)
    except (TypeError, ValueError):
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    try:
        board_service.update(
            user_id,
            payload.state,
            base_version=payload.base_version,
            allow_empty_overwrite=False,
        )
    except (BoardVersionConflictError, BoardUnsafeOverwriteError, BoardUnversionedUpdateError):
        # Conflicts/safeties are silent on the beacon path; the next live PUT
        # will reconcile properly.
        pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)
