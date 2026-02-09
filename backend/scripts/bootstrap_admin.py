from __future__ import annotations

import argparse

from sqlalchemy import or_, select

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()
    username = args.username.strip()

    with SessionLocal() as db:
        existing = db.execute(select(User).where(or_(User.email == email, User.username == username))).scalar_one_or_none()
        if existing is not None:
            raise SystemExit("User already exists")

        user = User(
            email=email,
            username=username,
            password_hash=get_password_hash(args.password),
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"created admin user id={user.id}")


if __name__ == "__main__":
    main()

