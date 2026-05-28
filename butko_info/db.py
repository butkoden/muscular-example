from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone

from .config import DATA_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD

_SCHEMA_READY_PATH = None


def connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return salt, digest.hex()


def verify_password(password, salt, digest):
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, digest)


def init_db():
    global _SCHEMA_READY_PATH
    current_db_path = str(DB_PATH)
    # Skip schema setup if this process already initialized the same DB path.
    if _SCHEMA_READY_PATH == current_db_path:
        return

    with connect() as conn:
        # WAL + NORMAL improves write/read concurrency for local SQLite usage.
        conn.execute("pragma journal_mode=WAL")
        conn.execute("pragma synchronous=NORMAL")
        conn.executescript(
            """
            create table if not exists settings (
                key text primary key,
                value text not null
            );

            create table if not exists bookings (
                id integer primary key autoincrement,
                name text not null,
                email text not null,
                title text not null,
                starts_at text not null,
                ends_at text not null,
                notes text not null default '',
                status text not null default 'pending',
                created_at text not null
            );
            """
        )
        row = conn.execute("select value from settings where key = 'admin_password_hash'").fetchone()
        if row is None:
            set_admin_password(DEFAULT_ADMIN_PASSWORD, conn=conn)
    _SCHEMA_READY_PATH = current_db_path


def set_admin_password(password, conn=None):
    own_conn = conn is None
    conn = conn or connect()
    try:
        salt, digest = hash_password(password)
        conn.execute(
            "insert or replace into settings(key, value) values('admin_password_salt', ?)",
            (salt,),
        )
        conn.execute(
            "insert or replace into settings(key, value) values('admin_password_hash', ?)",
            (digest,),
        )
        conn.commit()
    finally:
        if own_conn:
            conn.close()


def check_admin_password(password):
    init_db()
    with connect() as conn:
        rows = dict(conn.execute("select key, value from settings").fetchall())
    return verify_password(
        password,
        rows.get("admin_password_salt", ""),
        rows.get("admin_password_hash", ""),
    )


def create_booking(data):
    init_db()
    with connect() as conn:
        cursor = conn.execute(
            """
            insert into bookings(name, email, title, starts_at, ends_at, notes, status, created_at)
            values(?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                data["name"],
                data["email"],
                data["title"],
                data["starts_at"],
                data["ends_at"],
                data.get("notes", ""),
                now_iso(),
            ),
        )
        conn.commit()
        return get_booking(cursor.lastrowid)


def list_bookings(limit=50):
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "select * from bookings order by starts_at desc, id desc limit ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_booking(booking_id):
    with connect() as conn:
        row = conn.execute("select * from bookings where id = ?", (booking_id,)).fetchone()
    return dict(row) if row else None


def remove_booking(booking_id):
    init_db()
    booking = get_booking(booking_id)
    if booking is None:
        return None
    with connect() as conn:
        conn.execute("delete from bookings where id = ?", (booking_id,))
        conn.commit()
    return booking


def diagnostics():
    init_db()
    with connect() as conn:
        booking_count = conn.execute("select count(*) from bookings").fetchone()[0]
    return {
        "database": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "booking_count": booking_count,
        "time_utc": now_iso(),
    }
