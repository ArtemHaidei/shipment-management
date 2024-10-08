import logging

from uuid import UUID
from typing import Any
from sqlalchemy import select
from pydantic import field_validator, model_validator
from pydantic import BaseModel, Field, ConfigDict

from app.orm.database import async_session
from app.orm.models import Country, State, City
from app.exceptions.address import (
    CityStateMismatchError,
    CountryNotFoundError,
    StateNotFoundError,
    CityNotFoundError,
    StateCountryMismatchError,
    CityCountryMismatchError,
    CountryParametrError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ADDRESS SCHEMA")


# ============================= Country =============================
class CountryIn(BaseModel):
    """
    Represents the input of a country operation.

    Attributes:
        name (str): The name of the country.
        code (str): The numeric code of the country.
        iso2 (str): The ISO2 code of the country.
        iso3 (str): The ISO3 code of the country.
    """

    name: str = Field(..., max_length=100, min_length=2)
    code: str = Field(..., pattern="^[0-9]{3}$")
    iso2: str = Field(..., pattern="^[A-Za-z]{2}$")
    iso3: str = Field(..., pattern="^[A-Za-z]{3}$")

    @field_validator("iso2", "iso3", mode="before")  # noqa
    @classmethod
    def uppercase_country_code(cls, value: str) -> str:
        """Converts the country code to uppercase."""
        return value.upper()


class CountryOneField(BaseModel):
    """
    Represents a country with optional search fields.

    Attributes:
        name (str | None): The name of the country.
        code (str | None): The numeric code of the country.
        iso2 (str | None): The ISO2 code of the country.
        iso3 (str | None): The ISO3 code of the country.
    """

    model_config = ConfigDict(title="Country Search")
    name: str | None = Field(
        None,
        title="Country Name",
        max_length=100,
        min_length=2,
        examples=["United States", "Canada", "Mexico"],
    )
    code: str | None = Field(
        None,
        title="Country Code",
        description="The numeric code of the country.",
        pattern="^[0-9]{3}$",
        examples=["840", "124", "484"],
    )
    iso2: str | None = Field(
        None,
        title="Country ISO2",
        description="ISO2 code must be exactly 2 uppercase or lowercase letters.",
        pattern="^[A-Za-z]{2}$",
        examples=["US", "CA", "MX"],
    )
    iso3: str | None = Field(
        None,
        title="Country ISO3",
        description="ISO3 code must be exactly 3 uppercase or lowercase letters.",
        pattern="^[A-Za-z]{3}$",
        examples=["USA", "can", "MEX"],
    )

    @field_validator("iso2", "iso3", mode="before")  # noqa
    @classmethod
    def uppercase_country_code(cls, value: str) -> str:
        """Converts the country code to uppercase."""
        return value.upper() if value else None

    @model_validator(mode="after")
    def check_if_no_search_params(self):
        """
        Validates that at least one search parameter is provided.

        Raises:
            CountryParametrError: If no search parameters are provided.
        """
        if not any(self.model_dump().values()):
            raise CountryParametrError()
        return self

    def get_search_params(self) -> tuple[str, str]:
        """
        Retrieves the first non-null search parameter.

        Returns:
            tuple[str, str]: A tuple containing the field name and its value.
        """
        for key, value in self.model_dump().items():
            if value:
                return key, value


# ============================= In =============================
class StateIn(BaseModel):
    """
    Represents the input of a state operation.

    Attributes:
        name (str): The name of the state.
        country_id (UUID): The UUID of the country.
    """

    name: str = Field(
        ...,
        max_length=100,
        min_length=1,
    )
    country_id: UUID


class CityIn(BaseModel):
    """
    Represents the input of a city operation.

    Attributes:
        name (str): The name of the city.
        state_id (UUID): The UUID of the state.
        country_id (UUID): The UUID of the country.
    """

    name: str = Field(
        ...,
        max_length=100,
        min_length=1,
    )
    state_id: UUID
    country_id: UUID


class AddressId(BaseModel):
    """
    Represents the ID information of an address.

    Attributes:
        shipment (Any): The shipment associated with the address.
        city_id (UUID): The UUID of the city.
        state_id (UUID): The UUID of the state.
        country_id (UUID): The UUID of the country.
    """

    shipment: Any
    city_id: UUID
    state_id: UUID
    country_id: UUID


class AddressIn(BaseModel):
    """
    Represents the input of an address operation.

    Attributes:
        postal_code (str): The postal code of the address.
        address_line_1 (str): The first line of the address.
        address_line_2 (str | None): The second line of the address, if any.
        city (str): The name of the city.
        state (str): The name of the state.
        country (CountryOneField): The country information.
    """

    postal_code: str = Field(
        ...,
        title="Postal Code",
        description="The postal code must contain between 3 and 10 symbols.",
        pattern=r"^[A-Za-z0-9\- ]{3,10}$",
    )
    address_line_1: str = Field(
        ...,
        title="Address Line 1",
        description="The address line 1 must contain between 5 and 150 symbols.",
        pattern=r"^[A-Za-z0-9\s\.,'\-#/]{5,150}$",
        examples=["1234 Main St.", "Apt. 1234", "PO Box 1234"],
    )
    address_line_2: str | None = Field(
        None,
        title="Address Line 2",
        description="The address line 2 must contain between 5 and 150 symbols.",
        pattern=r"^[A-Za-z0-9\s\.,'\-#/]{5,150}$",
        examples=["Apt. 1234", "PO Box 1234"],
    )

    city: str = Field(
        ...,
        title="City Name",
        description="The city's name must contain at least 3 symbols and a maximum of 100.",
        max_length=100,
        min_length=1,
    )
    state: str = Field(
        ...,
        title="City Name",
        description="The city's name must contain at least 3 symbols and a maximum of 100.",
        max_length=100,
        min_length=1,
    )
    country: CountryOneField

    @field_validator("address_line_2", mode="before")  # noqa
    @classmethod
    def check_address_line_2(cls, value: str) -> str | None:
        """
        Validates the address line 2 field.

        Args:
            value (str): The value of the address line 2 field.

        Returns:
            str | None: The validated address line 2 or None if not provided.
        """
        return value if value else None

    async def check_if_country_state_city_exists(self, parent: Any) -> AddressId:
        """
        Checks if the country, state, and city exist in the database.

        Args:
            parent (Any): The parent object.

        Returns:
            AddressId: The address ID object containing the IDs of the city, state, and country.

        Raises:
            CountryNotFoundError: If the country is not found.
            StateNotFoundError: If the state is not found.
            CityNotFoundError: If the city is not found.
            StateCountryMismatchError: If the state does not belong to the country.
            CityStateMismatchError: If the city does not belong to the state.
            CityCountryMismatchError: If the city does not belong to the country.
        """
        async with async_session() as session:
            async with session.begin():
                field, value = self.country.get_search_params()
                country = await session.execute(
                    select(Country).filter(getattr(Country, field) == value)
                )
                country = country.scalars().first()

                if not country:
                    raise CountryNotFoundError(value)

                result = await session.execute(
                    select(State).filter_by(name=self.state, country_id=country.id)
                )
                state = result.scalars().first()
                if not state:
                    raise StateNotFoundError(self.state)

                if state.country_id != country.id:
                    raise StateCountryMismatchError(self.state, country.name)

                result = await session.execute(
                    select(City).filter_by(
                        name=self.city, state_id=state.id, country_id=country.id
                    )
                )
                city = result.scalars().first()
                if not city:
                    raise CityNotFoundError(self.city)

                if city.state_id != state.id:
                    raise CityStateMismatchError(self.city, self.state)

                if city.country_id != country.id:
                    raise CityCountryMismatchError(self.city, country.name)

        return AddressId(
            shipment=parent, city_id=city.id, state_id=state.id, country_id=country.id
        )


# ============================= OUT =============================
class AddressOut(BaseModel):
    """
    Represents the output of an address operation.

    Attributes:
        postal_code (str): The postal code of the address.
        address_line_1 (str): The first line of the address.
        address_line_2 (str | None): The second line of the address, if any.
        city (str): The name of the city.
        state (str): The name of the state.
        country (str): The code of the country.
    """

    model_config = ConfigDict(title="Address Out")
    postal_code: str = Field(..., examples=["12345"])
    address_line_1: str = Field(..., examples=["1234 Main St."])
    address_line_2: str | None = Field(None, examples=["Apt. 1234"])

    city: str = Field(..., examples=["New York"])
    state: str = Field(..., examples=["New York"])
    country: str = Field(..., examples=["USA"])

    @field_validator("country", mode="before")  # noqa
    @classmethod
    def retrive_code(cls, country) -> str:
        """
        Retrieves the Country code of the field.
        """
        return country.iso3

    @field_validator("city", "state", mode="before")  # noqa
    @classmethod
    def retrive_name(cls, field) -> str:
        """
        Retrieves the name of the field.
        """
        return field.name
