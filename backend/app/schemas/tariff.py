from datetime import date

from pydantic import BaseModel, Field


class TariffItems(BaseModel):
    start_price: float = Field(gt=0, description="起步价必须大于 0")
    start_include_km: float = Field(ge=0, description="含公里不能为负")
    per_km: float = Field(ge=0, description="每公里不能为负")
    per_slow_min: float = Field(ge=0, description="低速单价不能为负")
    night_factor: float = Field(ge=1, description="夜间系数不能小于 1")


class ScheduledTariffIn(TariffItems):
    effective_date: date
