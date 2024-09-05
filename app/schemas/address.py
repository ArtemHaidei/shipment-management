from uuid import UUID
from typing import Optional, Self
from sqlalchemy import select
from pydantic import field_validator, model_validator, create_model
from pydantic import BaseModel, Field, ConfigDict, ValidationError

from app.orm.database import async_session
from app.orm.models import Country, State, City


# ============================= Base =============================
class CountryBase(BaseModel):
    model_config = ConfigDict(title="Country Query", from_attributes=True)
    name: str = Field(
        ...,
        title="Country Name",
        description="The name of the country.",
        max_length=100,
        min_length=2,
    )
    code: str = Field(
        ...,
        title="Country Code",
        description="The numeric code of the country.",
        pattern="^[0-9]{3}$",
    )
    iso2: str = Field(
        ...,
        title="Country ISO2",
        description="ISO2 code must be exactly 2 uppercase or lowercase letters.",
        pattern="^[A-Za-z]{2}$",
    )
    iso3: str = Field(
        ...,
        title="Country ISO3",
        description="ISO3 code must be exactly 3 uppercase or lowercase letters.",
        pattern="^[A-Za-z]{3}$",
    )

    @field_validator("iso2", "iso3", mode="before")  # noqa
    @classmethod
    def uppercase_country_code(cls, value: str) -> str:
        return value.upper()


class CountryOptional(BaseModel):
    model_config = ConfigDict(title="Country Search")
    name: str | None
    code: str | None
    iso2: str | None
    iso3: str | None

    @model_validator(mode="before")
    @classmethod
    def check_if_no_search_params(cls, values: dict) -> None:
        if not any(values.values()):
            raise ValidationError(
                "At least one search parameter for Country must be provided."
            )

    def get_search_params(self) -> str:
        for key, value in self.model_dump().items():
            if value:
                return value


class StateBase(BaseModel):
    model_config = ConfigDict(title="State Base", from_attributes=True)
    name: str = Field(
        ...,
        title="State Name",
        description="The state's name must contain at least 3 symbols and a maximum of 100.",
        max_length=100,
        min_length=1,
    )


class CityBase(BaseModel):
    model_config = ConfigDict(title="City Base", from_attributes=True)
    name: str = Field(
        ...,
        title="City Name",
        description="The city's name must contain at least 3 symbols and a maximum of 100.",
        max_length=100,
        min_length=1,
    )


class AddressBase(BaseModel):
    model_config = ConfigDict(title="Address Base", from_attributes=True)
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


# ============================= Search =============================
CountryOneField = create_model(
    "CountryOptional",
    **{
        field: (Optional[type_], None)
        for field, type_ in CountryBase.__annotations__.items()
    },
    __base__=CountryOptional,
)


# ============================= In =============================
class StateIn(StateBase):
    model_config = ConfigDict(title="State In")
    """
    Model for creating a state record in the database.

    :param name: The name of the state.
    :param country_id: The UUID of the country.
    """
    country_id: UUID


class CityIn(CityBase):
    model_config = ConfigDict(title="City In")
    """
    Model for creating a city record in the database.

    :param name: The name of the city.
    :param state_id: The UUID of the state.
    :param country_id: The UUID of the country.
    """
    state_id: UUID
    country_id: UUID


class AddressIn(AddressBase):
    model_config = ConfigDict(title="Address In")
    city_id: UUID = None
    state_id: UUID = None
    country_id: UUID = None
    city: CityBase = Field(
        ...,
        title="City",
        description="The city where the address is located.",
        exclude=True,
    )
    state: StateBase = Field(
        ...,
        title="State",
        description="The state where the address is located.",
        exclude=True,
    )
    country: CountryOneField = Field(
        ...,
        title="Country",
        description="The country where the address is located.",
        exclude=True,
    )

    @model_validator(mode="after")
    async def check_if_country_state_city_exists(self) -> Self:
        async with async_session as session:
            async with session.begin():
                country_search_param = self.country.get_search_params()
                country = await session.execute(
                    select(Country).filter(
                        getattr(Country, country_search_param) == country_search_param
                    )
                )
                if not country:
                    raise ValidationError("Country does not exist.")

                result = await session.execute(
                    select(State).filter_by(name=self.state.name, country_id=country.id)
                )
                state = result.scalars().first()
                if not state:
                    raise ValidationError("State does not exist.")

                if state.country_id != country.id:
                    raise ValidationError(
                        "State does not belong to the provided country."
                    )
                result = await session.execute(
                    select(City).filter_by(
                        name=self.city.name, state_id=state.id, country_id=country.id
                    )
                )
                city = result.scalars().first()

                if not city:
                    raise ValidationError("City does not exist.")

                if city.state_id != state.id:
                    raise ValidationError("City does not belong to the provided state.")

                if city.country_id != country.id:
                    raise ValidationError(
                        "City does not belong to the provided country."
                    )

                self.city_id = city.id
                self.state_id = state.id
                self.country_id = country.id

        return self


# ============================= OUT =============================
# ----------------------------- Country -----------------------------
class CountryOutName(BaseModel):
    model_config = ConfigDict(title="Country Out", from_attributes=True)
    name: str


class CountryOutISO3(BaseModel):
    model_config = ConfigDict(title="Country Out ISO3", from_attributes=True)
    iso3: str


class CountryOutISO2(BaseModel):
    model_config = ConfigDict(title="Country Out ISO2", from_attributes=True)
    iso2: str


class CountryOutNumericCode(BaseModel):
    model_config = ConfigDict(title="Country Out Numeric Code", from_attributes=True)
    code: str


class CountryOut(CountryOutName, CountryOutISO3, CountryOutISO2, CountryOutNumericCode):
    model_config = ConfigDict(title="Country Out", from_attributes=True)
    ...


# ----------------------------- State -----------------------------
class StateOutName(BaseModel):
    model_config = ConfigDict(title="State Out", from_attributes=True)
    name: str


# ----------------------------- City -----------------------------
class CityOutName(BaseModel):
    model_config = ConfigDict(title="City Out", from_attributes=True)
    name: str


# ----------------------------- Address -----------------------------
class AddressOutBase(AddressBase):
    model_config = ConfigDict(title="Address Out", from_attributes=True)
    city: CityOutName
    state: StateOutName
    country: CountryOutISO3


class AddressOut(AddressOutBase):
    model_config = ConfigDict(title="Address Out", from_attributes=True)
    city: str = Field(
        ...,
        title="City",
        description="The city where the address is located.",
        examples=["New York", "Los Angeles", "Chicago"],
    )
    state: str = Field(
        ...,
        title="State",
        description="The state where the address is located.",
        examples=["California", "Texas", "Florida"],
    )
    country: str = Field(
        ...,
        title="Country",
        description="The country where the address is located.",
        examples=["USA", "Canada", "Mexico"],
    )

    @classmethod
    def out(cls, adrress: AddressOutBase) -> Self:
        fields = adrress.model_dump()
        fields["city"] = adrress.city.name
        fields["state"] = adrress.state.name
        fields["country"] = adrress.country.iso3
        return cls(**fields)
