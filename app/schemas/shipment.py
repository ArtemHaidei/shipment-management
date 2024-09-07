import logging
import re
from typing import Any

from uuid import UUID
from sqlalchemy import select
from pydantic import constr, field_validator
from pydantic import BaseModel, Field, ConfigDict

from app.orm.models import Carrier
from app.orm.database import async_session
from datetime import datetime, timezone
from app.choices import WeightUnit, DimensionsUnit, CurrencyEnum
from .address import AddressIn, AddressOut
from app.exceptions.shipment import (
    CarrierNotFoundError,
    ShipmentNumberMismatchError,
    ShipmentDateError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SHIPMENT SCHEMA")


class PackageIn(BaseModel):
    model_config = ConfigDict(
        title="Carrier Create",
    )

    weight: float = Field(
        ...,
        title="Weight",
        description="The weight of the package should be between 0.1 and 1,000,000.",
        gt=0.1,
        le=1_000_000,
        examples=[25, 10],
    )
    weight_unit: WeightUnit = Field(
        WeightUnit.GRAM,
        title="Weight Unit",
        description="The unit of the weight of the package, can be 'g', 'kg', or 'lb'.",
        examples=[WeightUnit.GRAM, WeightUnit.KG, WeightUnit.LB],
    )
    length: float = Field(
        ...,
        title="Length",
        description="The length of the package should be between 0.1 and 10,000.",
        gt=0.1,
        le=10_000,
        examples=[1.5, 5, 10],
    )
    width: float = Field(
        ...,
        title="Width",
        description="The width of the package should be between 0.1 and 10,000.",
        gt=0.1,
        le=10_000,
        examples=[5, 10],
    )
    height: float = Field(
        ...,
        title="Height",
        description="The height of the package should be between 0.1 and 10,000.",
        gt=0.1,
        le=10_000,
        examples=[10],
    )
    dimensions_unit: DimensionsUnit = Field(
        DimensionsUnit.CM,
        title="Dimensions Unit",
        description="The unit of the dimensions of the package, can be 'mm', 'cm', or 'in'.",
        examples=[DimensionsUnit.MM, DimensionsUnit.CM, DimensionsUnit.IN],
    )


# ============================= In =============================
class CarrierIn(BaseModel):
    model_config = ConfigDict(title="Carrier In")

    name: str = Field(
        ...,
        title="Carrier Name",
        description="The name of the carrier should be between 3 and 128 symbols.",
        max_length=128,
        min_length=3,
        examples=["ups", "fedex", "dhl-express"],
    )

    regex_tracking_number: dict[str, constr(pattern=r"^(?:\\.|[^\\])+$")] = Field(
        ...,
        title="Regex Tracking Number",
        description="The regex pattern for the tracking number of the carrier.",
        examples=[{"standard": r"^1Z[A-Za-z0-9]{16}$"}],
    )


class ShipmentIn(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    shipment_number: str = Field(
        ...,
        title="Shipment Number",
        description="The shipment number should be between a valid tracking number of the carrier.",
        max_length=40,
        min_length=3,
        examples=["1Z12345E1512345676", "1Z12345E1512345677"],
    )
    shipment_date: datetime = Field(
        ...,
        title="Shipment Date",
        description="The date when the shipment was picked up. In ISO 8601 format.",
    )
    price: float = Field(
        ...,
        title="Price",
        description="The price of the shipment should be between 0.1 and 1,000,000.",
        gt=0.1,
        le=1_000_000,
        examples=[45, 35.4, 12.07, 1045],
    )
    currency: CurrencyEnum = Field(
        ...,
        title="Currency",
        description="The currency of the price of the shipment.",
        examples=[CurrencyEnum.USD, CurrencyEnum.EUR, CurrencyEnum.GBP],
        validate_default=True,
    )
    total_weight: float = Field(
        ...,
        title="Total Weight",
        description="The total weight of the shipment should be between 0.1 and 1,000,000.",
        gt=0.1,
        le=1_000_000,
        examples=[0.5, 5, 12, 30],
    )
    total_weight_unit: WeightUnit = Field(
        WeightUnit.KG,
        title="Total Weight Unit",
        description="The unit of the total weight of the shipment, can be 'g', 'kg', or 'lb'.",
        examples=[WeightUnit.GRAM, WeightUnit.KG, WeightUnit.LB],
        validate_default=True,
    )

    carrier: str = Field(
        ...,
        title="Carrier Name",
        description="The name of the carrier should be between 3 and 128 symbols.",
        max_length=128,
        min_length=3,
        examples=["ups", "fedex", "dhl-express"],
    )
    address: AddressIn
    packages: list[PackageIn]

    @field_validator("shipment_date", mode="after")  # noqa
    @classmethod
    def check_if_not_in_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None and v.replace(tzinfo=timezone.utc) > datetime.now(
            timezone.utc
        ):
            raise ShipmentDateError()
        return v

    async def validate_carrier(self) -> Any:
        async with async_session() as session, session.begin():
            result = await session.execute(
                select(Carrier).where(Carrier.name == self.carrier)  # noqa
            )
            carrier: Carrier = result.scalar()

            if not carrier:
                return CarrierNotFoundError(self.carrier)

            patterns = carrier.regex_tracking_number.values()

            if not any(
                re.match(pattern=pattern, string=self.shipment_number)
                for pattern in patterns
            ):
                return ShipmentNumberMismatchError(self.carrier, self.shipment_number)

            return carrier


# ============================= OUT =============================
class PackageOut(BaseModel):
    id: UUID
    weight: float
    weight_unit: WeightUnit
    length: float
    width: float
    height: float
    dimensions_unit: DimensionsUnit


class ShipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID
    shipment_number: str
    shipment_date: datetime
    price: float
    currency: CurrencyEnum
    total_weight: float
    total_weight_unit: WeightUnit
    carrier: str
    address: AddressOut
    packages: list[PackageOut]

    @field_validator("currency", mode="before")  # noqa
    @classmethod
    def retrive_currency(cls, field) -> str:
        return field.code

    @field_validator("carrier", mode="before")  # noqa
    @classmethod
    def retrive_name(cls, field) -> str:
        return field.name


class ShipmentListOut(BaseModel):
    model_config = ConfigDict(title="Country Out")

    page: int = Field(
        ...,
        title="Page Number",
        description="The current page number.",
        ge=1,
    )
    next_page: int | None = Field(
        None,
        title="Next Page Number",
        description="The next page number.",
    )
    last_page: int = Field(
        ...,
        title="Last Page Number",
        description="The last page number.",
        ge=1,
    )
    limit: int = Field(
        ...,
        title="Items per Page",
        description="The number of items per page.",
        ge=1,
    )
    total: int = Field(
        ...,
        title="Total Items",
        description="The total number of items.",
    )
    items: int = Field(
        ...,
        title="Items",
        description="The number of items on the current page.",
    )
    records: list[ShipmentOut]


class PostOut(BaseModel):
    created: int
    message: str


class ShipmentPostOut(PostOut):
    model_config = ConfigDict(from_attributes=True)
    records: list[ShipmentOut]
