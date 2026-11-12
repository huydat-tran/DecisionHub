"""Router API cho module Auth."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.modules.auth.service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """Đăng ký tài khoản mới, mặc định được cấp role USER."""
    user = register_user(db, data)
    return RegisterResponse(message="Đăng ký thành công.", data=user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Đăng nhập và nhận access token",
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Đăng nhập bằng email và mật khẩu, trả về access token."""
    token_data = login_user(db, data)
    return LoginResponse(message="Đăng nhập thành công.", data=token_data)
