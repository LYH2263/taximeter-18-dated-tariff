import sqlite3
from datetime import datetime, timezone

from app.engines.tariff_schedule import FIVE


def get_active(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT * FROM tariff ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else {}


def update_active(conn: sqlite3.Connection, five: dict) -> dict:
    row = conn.execute("SELECT id FROM tariff ORDER BY id LIMIT 1").fetchone()
    vals = [five[k] for k in FIVE]
    if row:
        conn.execute(
            "UPDATE tariff SET start_price=?, start_include_km=?, per_km=?, per_slow_min=?, night_factor=? WHERE id=?",
            (*vals, row["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO tariff(start_price,start_include_km,per_km,per_slow_min,night_factor) VALUES (?,?,?,?,?)",
            vals,
        )
    conn.commit()
    return get_active(conn)


def get_scheduled(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM scheduled_tariff ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def replace_scheduled(conn: sqlite3.Connection, effective_date: str, five: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("DELETE FROM scheduled_tariff")
    conn.execute(
        "INSERT INTO scheduled_tariff(effective_date,start_price,start_include_km,per_km,per_slow_min,night_factor,created_at) VALUES (?,?,?,?,?,?,?)",
        (effective_date, *[five[k] for k in FIVE], now),
    )
    conn.commit()
    return get_scheduled(conn)
