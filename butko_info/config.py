from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("BUTKO_INFO_DB", DATA_DIR / "butko_info.sqlite3"))
ADMIN_SESSION_COOKIE = "butko_info_admin"
ADMIN_SESSION_VALUE = "local-admin-session"
DEFAULT_ADMIN_PASSWORD = os.environ.get("BUTKO_INFO_ADMIN_PASSWORD", "admin")
