from typing import Annotated
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import User


# Load application settings, including JWT configuration.
settings = get_settings()

# Read the Bearer token without automatically rejecting missing credentials.
bearer_scheme = HTTPBearer(auto_error=False)


# Reusable database dependency.
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: DbSession,
) -> User:
    """Validate the JWT and return the active user."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Reject requests without a Bearer token.
    if credentials is None:
        raise unauthorized

    try:
        # Decode and validate the JWT.
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # The token's subject must be a numeric user ID.
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdigit():
            raise unauthorized

    except jwt.InvalidTokenError:
        raise unauthorized from None

    # Retrieve the user from the database.
    user = db.get(User, int(subject))

    # Reject missing or deactivated users.
    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_roles(*allowed_roles: str) -> Callable:
    """Allow access only to users with an approved role."""

    # Normalize role names for consistent comparisons.
    permitted_roles = {
        role.strip().upper()
        for role in allowed_roles
    }

    def role_checker(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ) -> User:
        # Reject users who do not have an allowed role.
        if (
            current_user.role is None
            or current_user.role.name.upper() not in permitted_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    # Return the dependency function to FastAPI.
    return role_checker


# Reusable role-based dependencies.
# ADMIN can access admin-only resources.
AdminUser = Annotated[
    User,
    Depends(require_roles("ADMIN")),
]

# ADMIN and HR can access HR resources.
HRUser = Annotated[
    User,
    Depends(require_roles("ADMIN", "HR")),
]

# ADMIN and MANAGER can access manager resources.
ManagerUser = Annotated[
    User,
    Depends(require_roles("ADMIN", "MANAGER")),
]

# All authenticated roles can access general employee resources.
AuthenticatedUser = Annotated[
    User,
    Depends(
        require_roles("ADMIN", "HR", "MANAGER", "EMPLOYEE")
    ),
]
