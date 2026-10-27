
from fastapi import APIRouter, HTTPException, status , Depends
from sqlalchemy import select

from app.core.dependencies import DbSession , get_current_user
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    hash_password,
    hash_password_reset_token,
    verify_password,
)
from app.models import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.security import hash_password_reset_token
from app.models import PasswordResetToken
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> dict:
    email = str(payload.email).strip().lower()

    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    employee_role = db.scalar(
        select(Role).where(Role.name == "EMPLOYEE")
    )
    if employee_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default employee role is not configured",
        )

    user = User(
        email=email,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        hashed_password=hash_password(payload.password),
        role_id=employee_role.id,
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Registration successful. You can now log in.",
        "user_id": user.id,
        "email": user.email,
        "role": employee_role.name,
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(
        payload.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive",
        )

    if user.role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No role is assigned to this account",
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role.name,
    )

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role.name,
    )

@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the profile of the currently authenticated user."""

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.name,
        "is_active": current_user.is_active,
    }


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: DbSession,
) -> ForgotPasswordResponse:
    """Create a time-limited password-reset token."""

    generic_message = (
        "If an active account exists for this email, "
        "password-reset instructions have been generated."
    )

    settings = get_settings()
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    # Return the same public message for unknown/inactive accounts.
    if user is None or not user.is_active:
        return ForgotPasswordResponse(message=generic_message)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Invalidate earlier unused tokens for this user.
    previous_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()

    for old_token in previous_tokens:
        old_token.used_at = now

    raw_token = create_password_reset_token()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(raw_token),
        expires_at=now + timedelta(minutes=15),
    )

    try:
        db.add(reset_record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Only expose the raw token when explicitly enabled for development.
    return ForgotPasswordResponse(
        message=generic_message,
        reset_token=raw_token if settings.password_reset_debug else None,
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_password(
    payload: ResetPasswordRequest,
    db: DbSession,
) -> ResetPasswordResponse:
    """Validate a reset token and replace the account password."""

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    token_hash = hash_password_reset_token(payload.token)

    reset_record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    )

    if (
        reset_record is None
        or reset_record.used_at is not None
        or reset_record.expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password-reset token",
        )

    user = db.get(User, reset_record.user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password-reset token",
        )

    # Replace the old password with a secure hash.
    user.hashed_password = hash_password(payload.new_password)
    reset_record.used_at = now

    # Invalidate any other outstanding tokens for this user.
    other_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_record.id,
            PasswordResetToken.used_at.is_(None),
        )
    ).all()

    for other_token in other_tokens:
        other_token.used_at = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ResetPasswordResponse(
        message="Password reset successful. You can now log in."
    )
