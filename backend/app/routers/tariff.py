from fastapi import APIRouter

from app.schemas.tariff import ScheduledTariffIn, TariffItems
from app.services.taxi_service import TaxiService

router = APIRouter()


@router.get("/tariff")
def get_tariff():
    with TaxiService() as s:
        return s.tariff()


@router.post("/tariff/current")
def post_current_tariff(body: TariffItems):
    with TaxiService() as s:
        return {"current": s.update_current_tariff(body.model_dump())}


@router.post("/tariff/scheduled")
def post_scheduled_tariff(body: ScheduledTariffIn):
    with TaxiService() as s:
        return {"scheduled": s.update_scheduled_tariff(
            body.effective_date.isoformat(),
            body.model_dump(exclude={"effective_date"}),
        )}
