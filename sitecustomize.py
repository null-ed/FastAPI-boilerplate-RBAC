import os
import pathlib

# Ensure Alembic picks the config inside src, regardless of CWD
ROOT = pathlib.Path(__file__).resolve().parent
os.environ.setdefault("ALEMBIC_CONFIG", str(ROOT / "src" / "alembic.ini"))

# Keep admin disabled for tests without touching .env
os.environ.setdefault("CRUD_ADMIN_ENABLED", "False")