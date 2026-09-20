import sqlite3
from datetime import date

FIVE_KEYS = ("start_price", "start_include_km", "per_km", "per_slow_min", "night_factor")


def _five(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in FIVE_KEYS}


def get_active(conn: sqlite3.Connection) -> dict:
    row = conn.execute("SELECT * FROM tariff ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else {}


def get_scheduled(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM scheduled_tariff WHERE id = 1").fetchone()
    if not row:
        return None
    return {"effective_date": row["effective_date"], **_five(row)}


def get_bundle(conn: sqlite3.Connection) -> dict:
    return {"current": get_active(conn), "scheduled": get_scheduled(conn)}


def resolve_for_date(conn: sqlite3.Connection, service_date: date | None) -> tuple[dict, str]:
    """Pick the tariff for a service date.

    No date -> current; date on/after the scheduled effective date -> scheduled;
    otherwise current. Returns (five-item tariff dict, "current"|"scheduled").
    """
    if service_date is not None:
        sched = get_scheduled(conn)
        if sched is not None and service_date >= date.fromisoformat(sched["effective_date"]):
            return {k: sched[k] for k in FIVE_KEYS}, "scheduled"
    return {k: get_active(conn)[k] for k in FIVE_KEYS}, "current"


def upsert_current(conn: sqlite3.Connection, items: dict) -> dict:
    conn.execute(
        """INSERT INTO tariff(id,start_price,start_include_km,per_km,per_slow_min,night_factor)
           VALUES (1,:start_price,:start_include_km,:per_km,:per_slow_min,:night_factor)
           ON CONFLICT(id) DO UPDATE SET
             start_price=:start_price, start_include_km=:start_include_km,
             per_km=:per_km, per_slow_min=:per_slow_min, night_factor=:night_factor""",
        {k: items[k] for k in FIVE_KEYS},
    )
    conn.commit()
    return get_active(conn)


def upsert_scheduled(conn: sqlite3.Connection, effective_date: str, items: dict) -> dict:
    params = {"effective_date": effective_date, **{k: items[k] for k in FIVE_KEYS}}
    conn.execute(
        """INSERT INTO scheduled_tariff(id,effective_date,start_price,start_include_km,per_km,per_slow_min,night_factor)
           VALUES (1,:effective_date,:start_price,:start_include_km,:per_km,:per_slow_min,:night_factor)
           ON CONFLICT(id) DO UPDATE SET
             effective_date=:effective_date, start_price=:start_price,
             start_include_km=:start_include_km, per_km=:per_km,
             per_slow_min=:per_slow_min, night_factor=:night_factor""",
        params,
    )
    conn.commit()
    return get_scheduled(conn)
