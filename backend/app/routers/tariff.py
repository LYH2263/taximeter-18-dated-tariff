from fastapi import APIRouter
from app.schemas.tariff import CurrentTariffUpdate, ScheduledTariffUpsert
from app.services.taxi_service import TaxiService
router = APIRouter()
@router.get("/tariff")
def get_tariff():
    with TaxiService() as s: return s.tariff()
@router.put("/tariff")
def put_tariff(body: CurrentTariffUpdate):
    with TaxiService() as s: return s.update_tariff(body.five())
@router.put("/tariff/scheduled")
def put_scheduled_tariff(body: ScheduledTariffUpsert):
    with TaxiService() as s: return s.register_scheduled(body.effective_date, body.five())
