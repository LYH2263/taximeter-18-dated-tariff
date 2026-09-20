from datetime import date

FIVE = ("start_price", "start_include_km", "per_km", "per_slow_min", "night_factor")


def five_params(tariff: dict) -> dict:
    return {k: float(tariff[k]) for k in FIVE}


def pick_tariff(current: dict, scheduled: dict | None, service_date: date | None) -> tuple[dict, str]:
    """按服务日期取价：日期达到预约生效日则用预约五项，否则用现行五项；未给日期用现行。"""
    if service_date is not None and scheduled:
        effective = date.fromisoformat(scheduled["effective_date"])
        if service_date >= effective:
            return five_params(scheduled), "scheduled"
    return five_params(current), "current"
