from butko_info.cli import CliApp, expand_slash_args
from butko_info.db import create_booking, get_booking, init_db


def test_expand_slash_args():
    assert expand_slash_args(("bookings/remove", "1")) == ("bookings", "remove", "1")
    assert expand_slash_args(("set-password", "--password", "secret/value")) == (
        "set-password",
        "--password",
        "secret/value",
    )


def test_bookings_remove_command(monkeypatch, tmp_path):
    monkeypatch.setenv("BUTKO_INFO_DB", str(tmp_path / "test.sqlite3"))

    from butko_info import config
    from butko_info import db

    config.DB_PATH = tmp_path / "test.sqlite3"
    db.DB_PATH = config.DB_PATH
    db.DATA_DIR = tmp_path

    init_db()
    booking = create_booking({
        "name": "Denis",
        "email": "denis@example.test",
        "title": "Remove me",
        "starts_at": "2026-06-01T10:00:00+03:00",
        "ends_at": "2026-06-01T10:30:00+03:00",
        "notes": "",
    })

    app = CliApp()
    assert app.run("bookings", "remove", str(booking["id"])) is True
    assert get_booking(booking["id"]) is None
