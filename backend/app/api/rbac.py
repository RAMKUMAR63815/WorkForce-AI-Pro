
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import (
    DbSession,
    AdminUser,
    HRUser,
    ManagerUser,
    AuthenticatedUser,
)
from app.core.security import hash_password
from app.models import Role, User
from app.schemas.auth import (
    AdminCreateUserRequest,
    UpdateUserRoleRequest,
)

router = APIRouter(
    prefix="/rbac",
    tags=["Role-Based Access Control"],
)


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_role_user(
    payload: AdminCreateUserRequest,
    db: DbSession,
    current_user: AdminUser,
) -> dict:
    """Allow Admins to create HR and Manager accounts."""

    email = str(payload.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    role = db.scalar(
        select(Role).where(Role.name == payload.role)
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The {payload.role} role is not configured",
        )

    user = User(
        email=email,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        hashed_password=hash_password(payload.password),
        role_id=role.id,
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
        "message": "User created successfully",
        "user_id": user.id,
        "email": user.email,
        "role": role.name,
    }


@router.get("/admin-check")
def admin_check(current_user: AdminUser) -> dict:
    """Allow only Admin users."""

    return {
        "message": "Admin access granted",
        "email": current_user.email,
        "role": current_user.role.name,
    }


@router.get("/hr-check")
def hr_check(current_user: HRUser) -> dict:
    """Allow Admin and HR users."""

    return {
        "message": "HR access granted",
        "email": current_user.email,
        "role": current_user.role.name,
    }


@router.get("/manager-check")
def manager_check(current_user: ManagerUser) -> dict:
    """Allow Admin and Manager users."""

    return {
        "message": "Manager access granted",
        "email": current_user.email,
        "role": current_user.role.name,
    }


@router.get("/employee-check")
def employee_check(current_user: AuthenticatedUser) -> dict:
    """Allow all four authenticated roles."""

    return {
        "message": "Employee access granted",
        "email": current_user.email,
        "role": current_user.role.name,
    }
@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UpdateUserRoleRequest,
    db: DbSession,
    current_user: AdminUser,
):
    """Allow an administrator to update a user's role."""

    # Find the user whose role needs to change.
    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Never change an ADMIN account through this endpoint.
    if user.role.name == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator accounts cannot be changed through this endpoint.",
        )

    # Find the requested role in the database.
    role = db.scalar(
        select(Role).where(Role.name == payload.role)
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested role does not exist.",
        )

    # Update the foreign key connecting User to Role.
    user.role_id = role.id

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully.",
        "user_id": user.id,
        "email": user.email,
        "role": role.name,
    }