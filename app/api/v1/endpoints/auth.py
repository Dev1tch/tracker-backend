from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from uuid import UUID
from app.core.config import settings
from app.core.rate_limit import (
    enforce_login_email_limit,
    login_rate_limit,
    signup_rate_limit,
)
from app.core.security import create_access_token
from app.core.service_provider import ServiceProvider
from app.core.supabase_client import SupabaseClient
from app.services.project_service import ProjectService
from app.services.user_notification_service import UserNotificationService
from app.services.user_service import UserService
from app.schemas.user import User, UserCreate, Token

router = APIRouter()

@router.post("/signup", response_model=User, dependencies=[Depends(signup_rate_limit)])
def signup(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(ServiceProvider.get_user_service),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
    notifications: UserNotificationService = Depends(
        ServiceProvider.get_user_notification_service
    ),
):
    """Register a new user."""
    user = user_service.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )
    created = user_service.create(user_in)

    if created:
        project_service.accept_pending_invitations_for_user(
            user_id=UUID(created["id"]),
            email=created["email"],
        )
        background_tasks.add_task(
            notifications.send_welcome_email,
            recipient_email=created["email"],
            first_name=created.get("first_name"),
        )
        background_tasks.add_task(
            notifications.send_signup_notification,
            user_email=created["email"],
            first_name=created.get("first_name"),
        )

    return created

@router.post("/login", response_model=Token, dependencies=[Depends(login_rate_limit)])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(ServiceProvider.get_user_service),
    db: SupabaseClient = Depends(ServiceProvider.get_supabase_client),
):
    """OAuth2 compatible token login, get an access token for future requests."""
    # Per-account throttle (complements the per-IP limit on the route) to blunt
    # credential stuffing that rotates source IPs against one account.
    enforce_login_email_limit(db, form_data.username)
    user = user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user["id"], expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
