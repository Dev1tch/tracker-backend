from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.core.config import settings
from app.core.security import create_access_token
from app.core.service_provider import ServiceProvider
from app.services.user_service import UserService
from app.schemas.user import User, UserCreate, Token, UserLogin

router = APIRouter()

@router.post("/signup", response_model=User)
def signup(
    user_in: UserCreate,
    user_service: UserService = Depends(ServiceProvider.get_user_service)
):
    """Register a new user."""
    user = user_service.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )
    return user_service.create(user_in)

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(ServiceProvider.get_user_service)
):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = user_service.authenticate(
        UserLogin(email=form_data.username, password=form_data.password)
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user["id"], expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
