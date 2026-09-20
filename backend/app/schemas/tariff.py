from datetime import date

from pydantic import BaseModel, Field


class TariffFive(BaseModel):
    start_price: float = Field(ge=0)
    start_include_km: float = Field(ge=0)
    per_km: float = Field(ge=0)
    per_slow_min: float = Field(ge=0)
    night_factor: float = Field(gt=0)

    def five(self) -> dict:
        return self.model_dump()


class CurrentTariffUpdate(TariffFive):
    pass


class ScheduledTariffUpsert(TariffFive):
    effective_date: date
