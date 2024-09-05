import re
from uuid import UUID
from typing import Self
from datetime import datetime
from sqlalchemy import select
from pydantic import constr, field_validator, model_validator
from pydantic import BaseModel, Field, ConfigDict, ValidationError

from app.choices import WeightUnit, DimensionsUnit, CurrencyEnum
from .address import AddressIn, AddressOutBase, AddressOut
from app.orm.models import Carrier


from app.orm.database import async_session


# ============================= Base =============================
class CarrierBase(BaseModel):
    model_config = ConfigDict(title="Carrier Base")

    name: str = Field(
        ...,
        title="Carrier Name",
        description="The name of the carrier should be between 3 and 128 symbols.",
        max_length=128,
        min_length=3,
        examples=["UPS", "FedEx", "DHL Express"],
    )


class PackageBase(BaseModel):
    model_config = ConfigDict(
        title="Carrier Create", from_attributes=True, use_enum_values=True
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


class ShipmentBase(BaseModel):
    model_config = ConfigDict(
        title="Shipment Base", from_attributes=True, use_enum_values=True
    )

    shipment_number: str = Field(
        ...,
        title="Shipment Number",
        description="The shipment number should be between a valid tracking number of the carrier.",
        max_length=128,
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


# ============================= In =============================
# ----------------------------- Carrier -----------------------------
class CarrierIn(CarrierBase):
    model_config = ConfigDict(title="Carrier In")

    regex_tracking_number: dict[str, constr(pattern=r"^(?:\\.|[^\\])+$")] = Field(
        ...,
        title="Regex Tracking Number",
        description="The regex pattern for the tracking number of the carrier.",
        examples=[{"standard": r"^1Z[A-Za-z0-9]{16}$"}],
    )


# ----------------------------- Shipment -----------------------------
class ShipmentIn(ShipmentBase):
    model_config = ConfigDict(title="Shipment In", use_enum_values=True)
    carrier: CarrierIn = Field(
        ...,
        title="Carrier",
        description="The carrier of the shipment.",
        exclude=True,
    )
    carrier_id: UUID = None
    address: AddressIn
    packages: list[PackageBase]

    @field_validator("shipment_date")  # noqa
    @classmethod
    def check_if_not_in_future(cls, v: datetime) -> datetime:
        if v > datetime.now():
            raise ValidationError(
                "The date when the shipment was picked up cannot be in the future."
            )
        return v

    @model_validator(mode="after")  # noqa
    async def check_carrier_exists(self) -> Self:
        async with async_session as session:
            async with session.begin():
                result = await session.execute(
                    select(Carrier).where(name=self.carrier.name)
                )
                carrier: Carrier = result.scalar()

                if not carrier:
                    raise ValidationError(
                        f"Carrier \"{self.carrier.name}' does not exist."
                    )

                self.carrier_id = carrier.id

                for pattern in self.carrier.regex_tracking_number.values():
                    if not re.match(pattern=pattern, string=self.shipment_number):
                        raise ValidationError(
                            f'Shipment number does not match any patter of the carrier "{self.carrier.name}".'
                        )
        return self


# ============================= OUT =============================
class ShipmentOutBase(ShipmentBase):
    model_config = ConfigDict(title="Shipment Out Base", from_attributes=True, use_enum_values=True)

    carrier: CarrierBase
    address: AddressOutBase
    packages: list[PackageBase]


class ShipmentOut(ShipmentOutBase):
    model_config = ConfigDict(title="Shipment Out", from_attributes=True, use_enum_values=True)

    address: AddressOut
    carrier: str = Field(
        ...,
        title="Carrier",
        description="The carrier of the shipment.",
        examples=["UPS", "FedEx", "DHL Express"],
    )

    @classmethod
    def out(cls, shipment):
        fields = shipment.model_dump()
        fields["carrier"] = shipment.carrier.name
        fields["address"] = AddressOut.out(shipment.address).model_dump()
        return cls(**fields)


class ShipmentListOut(BaseModel):
    model_config = ConfigDict(title="Country Out", from_attributes=True, use_enum_values=True)

    shipments: list[ShipmentOut]
    page: int = Field(
        ...,
        title="Page Number",
        description="The current page number.",
        ge=1,
    )
    next_page: int = Field(
        None,
        title="Next Page Number",
        description="The next page number.",
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
