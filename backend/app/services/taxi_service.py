from app.db import connect
from app.engines.night_compare import compare_day_night
from app.engines.tariff_breakdown import calc_fare
from app.engines.tariff_schedule import pick_tariff
from app.repositories import runs, settings, tariff, trips

class TaxiService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_trips(self): return trips.list_all(self._c)
    def trip(self, tid): return trips.get(self._c, tid)
    def tariff(self):
        return {"current": tariff.get_active(self._c), "scheduled": tariff.get_scheduled(self._c)}
    def update_tariff(self, five: dict):
        return tariff.update_active(self._c, five)
    def register_scheduled(self, effective_date, five: dict):
        return tariff.replace_scheduled(self._c, effective_date.isoformat(), five)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def fare(self, distance_km, slow_min, night, trip_id, persist, service_date=None):
        t, source = pick_tariff(tariff.get_active(self._c), tariff.get_scheduled(self._c), service_date)
        r = calc_fare(distance_km, slow_min, night, t)
        date_str = service_date.isoformat() if service_date else None
        result = {**r, "service_date": date_str, "tariff_source": source, "tariff": t}
        payload = {"distance_km": distance_km, "slow_min": slow_min, "night": night, "service_date": date_str}
        rid = runs.insert(self._c, "fare", payload, result, trip_id) if persist else None
        return {"run_id": rid, **result}
    def compare(self, distance_km, slow_min, persist):
        t = tariff.get_active(self._c)
        r = compare_day_night(distance_km, slow_min, t)
        rid = runs.insert(self._c, "compare", {"distance_km": distance_km, "slow_min": slow_min}, r, None) if persist else None
        return {"run_id": rid, **r}
    def dashboard(self):
        items = trips.list_all(self._c)
        clean = [x for x in items if "种子" not in x["label"]]
        dirty = [x for x in items if "种子" in x["label"]]
        return {"trip_count": len(items), "clean": len(clean), "dirty": len(dirty)}
