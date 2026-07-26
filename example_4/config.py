from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("MUSCULAR_EXAMPLE_DB", DATA_DIR / "example_4.sqlite3"))
ADMIN_SESSION_COOKIE = "example_4_admin"
ADMIN_SESSION_VALUE = "local-admin-session"
DEFAULT_ADMIN_PASSWORD = os.environ.get("MUSCULAR_EXAMPLE_ADMIN_PASSWORD", "admin")
