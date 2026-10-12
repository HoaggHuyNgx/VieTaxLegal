"""Promote an existing user to admin (there is deliberately no HTTP path to the first admin).

From backend/: .venv/Scripts/python.exe scripts/create_admin.py you@example.com
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.user import ROLE_ADMIN, User  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    args = parser.parse_args()
    with SessionLocal() as database:
        user = database.scalar(select(User).where(User.email == args.email.strip().lower()))
        if user is None:
            print("No user with that email. Register it first.", file=sys.stderr)
            return 1
        user.role = ROLE_ADMIN
        database.commit()
    print(f"{args.email} is now an admin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
