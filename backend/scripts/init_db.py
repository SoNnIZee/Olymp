from __future__ import annotations

from app.core.db import engine
from app.models import Base  # noqa: F401  (imports models for metadata)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("db initialized")


if __name__ == "__main__":
    main()

