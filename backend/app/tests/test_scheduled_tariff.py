import json
from datetime import date

import pytest
from pydantic import ValidationError

from app.repositories import tariff as tariff_repo
from app.schemas.tariff import ScheduledTariffIn, TariffItems
from app.services.taxi_service import TaxiService

SCHED_ITEMS = {"start_price": 13, "start_include_km": 3, "per_km": 2.8,
               "per_slow_min": 1, "night_factor": 1.3}
EFFECTIVE = "2026-10-01"


def register_scheduled(effective_date=EFFECTIVE, items=None):
    """Mirror the router: validate first, only touch the DB if validation passes."""
    body = ScheduledTariffIn(effective_date=effective_date, **(items or SCHED_ITEMS))
    with TaxiService() as s:
        return s.update_scheduled_tariff(body.effective_date.isoformat(),
                                         body.model_dump(exclude={"effective_date"}))


def test_register_and_read_scheduled():
    assert register_scheduled() == {"effective_date": EFFECTIVE, **SCHED_ITEMS}
    with TaxiService() as s:
        assert s.tariff()["scheduled"] == {"effective_date": EFFECTIVE, **SCHED_ITEMS}
        assert s.tariff()["current"]["start_price"] == 11


@pytest.mark.parametrize("bad", [
    {"start_price": 0}, {"start_price": -1}, {"per_km": -0.1},
    {"start_include_km": -1}, {"per_slow_min": -2}, {"night_factor": 0.9},
])
def test_invalid_items_rejected(bad):
    items = {**SCHED_ITEMS, **bad}
    with pytest.raises(ValidationError):
        ScheduledTariffIn(effective_date=EFFECTIVE, **items)
    with TaxiService() as s:
        assert s.tariff()["scheduled"] is None


def test_invalid_date_rejected():
    with pytest.raises(ValidationError):
        ScheduledTariffIn(effective_date="10/01/2026", **SCHED_ITEMS)


def test_fare_without_date_uses_current():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, True)
    assert r["tariff_source"] == "current"
    assert r["total"] == 25.9
    assert set(r["tariff"]) == set(tariff_repo.FIVE_KEYS)
    assert "effective_date" not in r


def test_fare_before_effective_uses_current():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, True, date(2026, 9, 30))
    assert r["tariff_source"] == "current"
    assert r["total"] == 25.9


def test_fare_on_effective_day_uses_scheduled():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, True, date(2026, 10, 1))
    assert r["tariff_source"] == "scheduled"
    assert r["effective_date"] == EFFECTIVE
    assert r["total"] == 30.0
    assert r["tariff"]["start_price"] == 13
    assert r["tariff"]["per_km"] == 2.8


def test_fare_after_effective_uses_scheduled():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, False, date(2026, 10, 2))
    assert r["tariff_source"] == "scheduled"
    assert r["total"] == 30.0


def test_readonly_on_effective_day_writes_nothing():
    register_scheduled()
    with TaxiService() as s:
        before = len(s.history(100))
        r = s.fare(8, 3, False, None, False, date(2026, 10, 1))
        after = len(s.history(100))
    assert r["tariff_source"] == "scheduled"
    assert r["run_id"] is None
    assert after == before


def test_persisted_run_snapshots_five_items():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, True, date(2026, 10, 1))
        row = next(x for x in s.history(100) if x["id"] == r["run_id"])
    stored_result = json.loads(row["result_json"])
    stored_input = json.loads(row["input_json"])
    assert stored_result["tariff_source"] == "scheduled"
    assert stored_result["tariff"] == SCHED_ITEMS
    assert stored_result["effective_date"] == EFFECTIVE
    assert stored_input["service_date"] == EFFECTIVE


def test_editing_scheduled_keeps_old_run_unchanged():
    register_scheduled()
    with TaxiService() as s:
        r = s.fare(8, 3, False, None, True, date(2026, 10, 1))
        old_row = next(x for x in s.history(100) if x["id"] == r["run_id"])
        old_result = old_row["result_json"]
    new_items = {**SCHED_ITEMS, "start_price": 20, "per_km": 3.5}
    register_scheduled(items=new_items)
    with TaxiService() as s:
        kept = next(x for x in s.history(100) if x["id"] == r["run_id"])
    assert kept["result_json"] == old_result
    assert json.loads(kept["result_json"])["tariff"] == SCHED_ITEMS
    with TaxiService() as s2:
        assert s2.tariff()["scheduled"]["start_price"] == 20


def test_update_current_tariff():
    items = TariffItems(start_price=15, start_include_km=2, per_km=3,
                        per_slow_min=1.5, night_factor=1.4)
    with TaxiService() as s:
        row = s.update_current_tariff(items.model_dump())
    assert row["start_price"] == 15
    with TaxiService() as s:
        assert s.tariff()["current"]["night_factor"] == 1.4


def test_update_current_validation():
    with pytest.raises(ValidationError):
        TariffItems(start_price=0, start_include_km=3, per_km=2.5,
                    per_slow_min=0.8, night_factor=1.2)
