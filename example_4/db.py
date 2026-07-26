from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timezone

from .config import DATA_DIR, DB_PATH, DEFAULT_ADMIN_PASSWORD

_SCHEMA_READY_PATH = None


def connect():
    # RU: Демо хранит SQLite-файл в data/, поэтому директорию создаем лениво.
    # EN: The demo stores SQLite in data/, so the directory is created lazily.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    # RU: sqlite3.Row позволяет обращаться к колонкам по имени.
    # EN: sqlite3.Row lets us access columns by name.
    conn.row_factory = sqlite3.Row
    return conn


def now_iso():
    # RU: Храним время в UTC, чтобы диагностика не зависела от локальной зоны.
    # EN: Store time in UTC so diagnostics do not depend on the local timezone.
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hash_password(password, salt=None):
    # RU: Для учебного примера не нужен внешний auth-сервис, но пароль все равно
    # храним как PBKDF2 hash, а не как plain text.
    # EN: The learning example does not need an external auth service, but the
    # password is still stored as a PBKDF2 hash, never as plain text.
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return salt, digest.hex()


def verify_password(password, salt, digest):
    _, candidate = hash_password(password, salt)
    # RU: compare_digest защищает от timing attacks в сравнении hash-строк.
    # EN: compare_digest protects hash-string comparison from timing attacks.
    return hmac.compare_digest(candidate, digest)


def init_db():
    global _SCHEMA_READY_PATH
    current_db_path = str(DB_PATH)
    # RU: Не повторяем schema setup, если этот процесс уже подготовил тот же файл.
    # EN: Skip schema setup if this process already initialized the same DB file.
    if _SCHEMA_READY_PATH == current_db_path:
        return

    with connect() as conn:
        # RU: WAL + NORMAL удобны для локального demo: чтение и запись меньше мешают друг другу.
        # EN: WAL + NORMAL are handy for local demos: reads and writes block each other less.
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
            # RU: Первый запуск сам создает admin password из config.py.
            # EN: First run creates the admin password from config.py.
            set_admin_password(DEFAULT_ADMIN_PASSWORD, conn=conn)
    _SCHEMA_READY_PATH = current_db_path


def set_admin_password(password, conn=None):
    # RU: conn можно передать снаружи, чтобы использовать одну транзакцию в init_db().
    # EN: conn can be passed in to reuse one transaction inside init_db().
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
    # RU: Проверка пароля всегда начинается с init_db(), чтобы тесты были автономными.
    # EN: Password checks always start with init_db() so tests are self-contained.
    init_db()
    with connect() as conn:
        rows = dict(conn.execute("select key, value from settings").fetchall())
    return verify_password(
        password,
        rows.get("admin_password_salt", ""),
        rows.get("admin_password_hash", ""),
    )


def create_booking(data):
    # RU: Валидация email уже была в Booking schema, здесь только persistence.
    # EN: Email validation already happened in the Booking schema; this is persistence only.
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
    # RU: limit защищает админскую страницу от слишком большого ответа.
    # EN: limit protects the admin page from overly large responses.
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
    # RU: Возвращаем удаленную запись, чтобы CLI мог напечатать понятное сообщение.
    # EN: Return the deleted row so CLI can print a helpful message.
    init_db()
    booking = get_booking(booking_id)
    if booking is None:
        return None
    with connect() as conn:
        conn.execute("delete from bookings where id = ?", (booking_id,))
        conn.commit()
    return booking


def diagnostics():
    # RU: Diagnostics endpoint показывает состояние demo без раскрытия секретов.
    # EN: The diagnostics endpoint shows demo state without exposing secrets.
    init_db()
    with connect() as conn:
        booking_count = conn.execute("select count(*) from bookings").fetchone()[0]
    return {
        "database": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "booking_count": booking_count,
        "time_utc": now_iso(),
    }
