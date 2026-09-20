import json
import os
import sqlite3
import tempfile
from datetime import date

import pytest

os.environ["DATA_DIR"] = tempfile.mkdtemp()

from app.engines.tariff_schedule import pick_tariff
from app.services import taxi_service

CURRENT = {"start_price": 11, "start_include_km": 3, "per_km": 2.5, "per_slow_min": 0.8, "night_factor": 1.2}
SCHED_ROW = {"effective_date": "2026-10-01", "start_price": 13, "start_include_km": 2, "per_km": 3.0, "per_slow_min": 1.0, "night_factor": 1.3}
SCHED_FIVE = {"start_price": 13, "start_include_km": 2, "per_km": 3.0, "per_slow_min": 1.0, "night_factor": 1.3}

SCHEMA = """
CREATE TABLE tariff(id INTEGER PRIMARY KEY, start_price REAL, start_include_km REAL, per_km REAL, per_slow_min REAL, night_factor REAL);
CREATE TABLE scheduled_tariff(id INTEGER PRIMARY KEY, effective_date TEXT, start_price REAL, start_include_km REAL, per_km REAL, per_slow_min REAL, night_factor REAL, created_at TEXT);
CREATE TABLE calc_runs(id INTEGER PRIMARY KEY, kind TEXT, trip_id INTEGER, input_json TEXT, result_json TEXT, created_at TEXT);
"""


@pytest.fixture
def svc(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO tariff(start_price,start_include_km,per_km,per_slow_min,night_factor) VALUES (11,3,2.5,0.8,1.2)")
    conn.commit()
    monkeypatch.setattr(taxi_service, "connect", lambda: conn)
    s = taxi_service.TaxiService()
    yield s
    s.close()


def register(svc):
    return svc.register_scheduled(date(2026, 10, 1), SCHED_FIVE)


# --- 取价引擎 ---
def test_pick_before_effective_uses_current():
    t, src = pick_tariff(CURRENT, SCHED_ROW, date(2026, 9, 30))
    assert src == "current" and t["start_price"] == 11

def test_pick_on_effective_day_uses_scheduled():
    t, src = pick_tariff(CURRENT, SCHED_ROW, date(2026, 10, 1))
    assert src == "scheduled" and t["start_price"] == 13

def test_pick_after_effective_uses_scheduled():
    t, src = pick_tariff(CURRENT, SCHED_ROW, date(2026, 12, 31))
    assert src == "scheduled"

def test_pick_without_date_uses_current():
    t, src = pick_tariff(CURRENT, SCHED_ROW, None)
    assert src == "current"

def test_pick_without_scheduled_uses_current():
    t, src = pick_tariff(CURRENT, None, date(2026, 12, 31))
    assert src == "current"


# --- 服务层：只读与快照 ---
def test_readonly_on_effective_day_uses_scheduled_and_writes_nothing(svc):
    register(svc)
    r = svc.fare(10, 5, False, None, False, date(2026, 10, 1))
    assert r["tariff_source"] == "scheduled"
    assert r["total"] == 42.0  # 13 + (10-2)*3 + 5*1
    assert r["run_id"] is None
    assert svc.history() == []

def test_persisted_record_keeps_five_snapshot_after_scheduled_change(svc):
    register(svc)
    r1 = svc.fare(10, 5, False, None, True, date(2026, 10, 2))
    assert r1["tariff_source"] == "scheduled"
    svc.register_scheduled(date(2026, 10, 1), {"start_price": 20, "start_include_km": 1, "per_km": 5.0, "per_slow_min": 2.0, "night_factor": 1.5})
    hist = svc.history()
    assert len(hist) == 1
    result = json.loads(hist[0]["result_json"])
    assert result["tariff_source"] == "scheduled"
    assert result["tariff"] == {k: float(v) for k, v in SCHED_FIVE.items()}  # 旧记录五项不动
    assert result["total"] == r1["total"]
    r2 = svc.fare(10, 5, False, None, False, date(2026, 10, 2))
    assert r2["tariff"]["start_price"] == 20.0  # 新计算用新五项

def test_no_date_uses_current(svc):
    register(svc)
    r = svc.fare(10, 5, False, None, False)
    assert r["tariff_source"] == "current"
    assert r["tariff"]["start_price"] == 11.0

def test_before_effective_persisted_uses_current(svc):
    register(svc)
    r = svc.fare(10, 5, False, None, True, date(2026, 9, 20))
    assert r["tariff_source"] == "current"
    result = json.loads(svc.history()[0]["result_json"])
    assert result["tariff"]["start_price"] == 11.0


# --- 校验：失败不登记 ---
def test_invalid_scheduled_rejected_by_schema():
    from pydantic import ValidationError
    from app.schemas.tariff import ScheduledTariffUpsert
    with pytest.raises(ValidationError):
        ScheduledTariffUpsert(effective_date="2026-10-01", start_price=-1, start_include_km=2, per_km=3, per_slow_min=1, night_factor=1.3)
    with pytest.raises(ValidationError):
        ScheduledTariffUpsert(effective_date="not-a-date", start_price=13, start_include_km=2, per_km=3, per_slow_min=1, night_factor=1.3)
    with pytest.raises(ValidationError):
        ScheduledTariffUpsert(effective_date="2026-10-01", start_price=13, start_include_km=2, per_km=3, per_slow_min=1, night_factor=0)


# --- API 端到端 ---
@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c

VALID_SCHED = {"effective_date": "2026-10-01", **SCHED_FIVE}

def test_api_invalid_scheduled_not_registered(client):
    bad = {**VALID_SCHED, "night_factor": 0}
    assert client.put("/api/tariff/scheduled", json=bad).status_code == 422
    assert client.get("/api/tariff").json()["scheduled"] is None

def test_api_fare_by_date_and_snapshot(client):
    assert client.put("/api/tariff/scheduled", json=VALID_SCHED).status_code == 200
    r = client.post("/api/fare", json={"distance_km": 10, "slow_min": 5, "night": False, "persist": False, "service_date": "2026-10-01"})
    body = r.json()
    assert body["tariff_source"] == "scheduled" and body["total"] == 42.0 and body["run_id"] is None
    assert body["tariff"]["start_price"] == 13.0
    r = client.post("/api/fare", json={"distance_km": 10, "slow_min": 5, "night": False, "persist": False})
    assert r.json()["tariff_source"] == "current"
    r = client.post("/api/fare", json={"distance_km": 10, "slow_min": 5, "night": False, "persist": True, "service_date": "2026-10-02"})
    rid = r.json()["run_id"]
    assert rid
    client.put("/api/tariff/scheduled", json={**VALID_SCHED, "start_price": 99})
    rec = [h for h in client.get("/api/history").json()["items"] if h["id"] == rid][0]
    result = json.loads(rec["result_json"])
    assert result["tariff"]["start_price"] == 13.0  # 快照不随改价变动
    assert result["tariff_source"] == "scheduled"
