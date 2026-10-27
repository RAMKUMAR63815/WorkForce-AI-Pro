
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Role


DEFAULT_ROLES = [
    {
        "name": "ADMIN",
        "description": "Manages the entire platform",
    },
    {
        "name": "HR",
        "description": "Manages employees and HR operations",
    },
    {
        "name": "MANAGER",
        "description": "Views team and workforce information",
    },
    {
        "name": "EMPLOYEE",
        "description": "Accesses personal employee information",
    },
]


def seed_initial_roles() -> None:
    """Create default roles without duplicating existing records."""
    with SessionLocal() as db:
        try:
            for role_data in DEFAULT_ROLES:
                existing_role = db.scalar(
                    select(Role).where(
                        Role.name == role_data["name"]
                    )
                )

                if existing_role is None:
                    db.add(Role(**role_data))

            db.commit()

        except Exception:
            db.rollback()
            raise
