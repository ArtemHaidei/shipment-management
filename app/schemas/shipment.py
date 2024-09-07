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
    """
    Represents the input of a package operation.

    Attributes:
        weight (float): The weight of the package.
        weight_unit (WeightUnit): The unit of the weight.
        length (float): The length of the package.
        width (float): The width of the package.
        height (float): The height of the package.
        dimensions_unit (DimensionsUnit): The unit of the dimensions.
    """

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
    """
    Represents the input of a carrier operation.

    Attributes:
        name (str): The name of the carrier.
        regex_tracking_number (dict[str, constr]): The regex pattern for the tracking number of the carrier.
    """

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
    """
    Represents the input of a shipment operation.

    Attributes:
        shipment_number (str): The shipment number.
        shipment_date (datetime): The date when the shipment was picked up.
        price (float): The price of the shipment.
        currency (CurrencyEnum): The currency of the price.
        total_weight (float): The total weight of the shipment.
        total_weight_unit (WeightUnit): The unit of the total weight.
        carrier (str): The name of the carrier.
        address (AddressIn): The address associated with the shipment.
        packages (list[PackageIn]): A list of packages included in the shipment.
    """

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
        """
        Validates that the shipment date is not in the future.

        Args:
            v (datetime): The shipment date.

        Raises:
            ShipmentDateError: If the shipment date is in the future.

        Returns:
            datetime: The validated shipment date.
        """
        if v.tzinfo is None and v.replace(tzinfo=timezone.utc) > datetime.now(
            timezone.utc
        ):
            raise ShipmentDateError()
        return v

    async def validate_carrier(self) -> Any:
        """
        Validates the carrier and the shipment number against the carrier's regex patterns.

        Returns:
            Carrier: The validated carrier object.

        Raises:
            CarrierNotFoundError: If the carrier is not found.
            ShipmentNumberMismatchError: If the shipment number does not match the carrier's regex patterns.
        """
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
    """
    Represents the output of a package operation.

    Attributes:
        id (UUID): The unique identifier of the package.
        weight (float): The weight of the package.
        weight_unit (WeightUnit): The unit of the weight.
        length (float): The length of the package.
        width (float): The width of the package.
        height (float): The height of the package.
        dimensions_unit (DimensionsUnit): The unit of the dimensions.
    """

    id: UUID = Field(..., examples=["0191ca45-ce30-4040-a269-74bd3966f180"])
    weight: float = Field(..., examples=[25])
    weight_unit: WeightUnit = Field(..., examples=[WeightUnit.GRAM])
    length: float = Field(..., examples=[1.5])
    width: float = Field(..., examples=[5])
    height: float = Field(..., examples=[10])
    dimensions_unit: DimensionsUnit = Field(..., examples=[DimensionsUnit.CM])


class ShipmentOut(BaseModel):
    """
    Represents the output of a shipment operation.

    Attributes:
        id (UUID): The unique identifier of the shipment.
        shipment_number (str): The shipment number.
        shipment_date (datetime): The date when the shipment was picked up.
        price (float): The price of the shipment.
        currency (CurrencyEnum): The currency of the price.
        total_weight (float): The total weight of the shipment.
        total_weight_unit (WeightUnit): The unit of the total weight.
        carrier (str): The name of the carrier.
        address (AddressOut): The address associated with the shipment.
        packages (list[PackageOut]): A list of packages included in the shipment.
    """

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID = Field(..., examples=["0191ca45-ce30-4040-a269-74bd3966f180"])
    shipment_number: str = Field(..., examples=["1Z12345E1512345676"])
    shipment_date: datetime = Field(..., examples=["2021-10-01T12:00:00Z"])
    price: float = Field(..., examples=[45])
    currency: CurrencyEnum = Field(..., examples=[CurrencyEnum.USD])
    total_weight: float = Field(..., examples=[0.5])
    total_weight_unit: WeightUnit = Field(..., examples=[WeightUnit.GRAM])
    carrier: str = Field(..., examples=["ups"])
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
    """
    Represents the output of a shipment list operation.

    Attributes:
        page (int): The current page number.
        next_page (int | None): The next page number, if available.
        last_page (int): The last page number.
        limit (int): The number of items per page.
        total (int): The total number of items.
        items (int): The number of items on the current page.
        records (list[ShipmentOut]): A list of shipment records on the current page.
    """

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
    """
    Represents the output of a post operation.

    Attributes:
        created (int): The number of created records.
        message (str): A message indicating the result of the operation.
    """

    created: int
    message: str


class ShipmentPostOut(PostOut):
    """
    Represents the output of a shipment post operation, inheriting from PostOut.

    Attributes:
        records (list[ShipmentOut]): A list of created shipment records.
    """

    model_config = ConfigDict(from_attributes=True)
    records: list[ShipmentOut]
