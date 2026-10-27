
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Role, User


def main() -> None:
    """Create the first administrator interactively."""
    email = input("Admin email: ").strip().lower()
    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()

    if not email or not first_name or not last_name:
        print("Error: all fields are required.")
        return

    password = getpass("Admin password (minimum 12 characters): ") #When you type your password, the characters are hidden on the terminal
    confirmation = getpass("Confirm password: ")

    if len(password) < 12:
        print("Error: password must contain at least 12 characters.")
        return

    if len(password) > 128:
        print("Error: password must not exceed 128 characters.")
        return

    if password != confirmation:
        print("Error: passwords do not match.")
        return

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print("Error: an account with this email already exists.")
            return

        admin_role = db.scalar(
            select(Role).where(Role.name == "ADMIN")
        )

        if admin_role is None:
            print("Error: ADMIN role not found. Run role seeding first.")
            return

        admin = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password),
            role_id=admin_role.id,
            is_active=True,
        )

        try:
            db.add(admin)
            db.commit()
            print(f"Administrator created successfully: {email}")
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
