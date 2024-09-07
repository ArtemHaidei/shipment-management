import logging

from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy_utils import CurrencyType, Timestamp

from app.choices import DimensionsUnit, WeightUnit
from .database import Base
from .utils import make_uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MODELS")


class Country(Base):
    """
    Represents a country in the database.

    Attributes:
        id (UUID): The unique identifier for the country.
        name (str): The name of the country.
        code (int): The numeric code of the country.
        iso2 (str): The ISO 3166-1 alpha-2 code of the country.
        iso3 (str): The ISO 3166-1 alpha-3 code of the country.
        states (relationship): The relationship to the State model.
        cities (relationship): The relationship to the City model.
        addresses (relationship): The relationship to the Address model.
    """

    __tablename__ = "countries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    name = Column(String(100), nullable=False)
    code = Column(String(3), nullable=False)
    iso2 = Column(String(2), nullable=False)
    iso3 = Column(String(3), nullable=False)

    states = relationship("State", back_populates="country")
    cities = relationship("City", back_populates="country")
    addresses = relationship("Address", back_populates="country")

    def __repr__(self):
        """
        Returns a string representation of the Country instance.

        Returns:
            str: A string in the format <Country {self.name}>.
        """
        return f"<Country {self.name}>"

    def __str__(self):
        """
        Returns the name of the country.

        Returns:
            str: The name of the country.
        """
        return self.name


class State(Base):
    """
    Represents a state in the database.

    Attributes:
        id (UUID): The unique identifier for the state.
        name (str): The name of the state.
        country_id (UUID): The foreign key referencing the country.
        country (relationship): The relationship to the Country model.
        cities (relationship): The relationship to the City model.
        addresses (relationship): The relationship to the Address model.
    """

    __tablename__ = "states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    name = Column(String(100), nullable=False, index=True)

    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    country = relationship("Country", back_populates="states")

    cities = relationship("City", back_populates="state")

    addresses = relationship("Address", back_populates="state")

    def __repr__(self):
        """
        Returns a string representation of the State instance.

        Returns:
            str: A string in the format <State {self.name}>.
        """
        return f"<State {self.name}>"

    def __str__(self):
        """
        Returns the name of the state.

        Returns:
            str: The name of the state.
        """
        return self.name


class City(Base):
    """
    Represents a city in the database.

    Attributes:
        id (UUID): The unique identifier for the city.
        name (str): The name of the city.
        country_id (UUID): The foreign key referencing the country.
        country (relationship): The relationship to the Country model.
        state_id (UUID): The foreign key referencing the state.
        state (relationship): The relationship to the State model.
        addresses (relationship): The relationship to the Address model.
    """

    __tablename__ = "cities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    name = Column(String(100), nullable=False, index=True)

    country_id = Column(
        UUID(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE")
    )
    country = relationship("Country", back_populates="cities")

    state_id = Column(
        UUID(as_uuid=True), ForeignKey("states.id", ondelete="CASCADE"), index=True
    )
    state = relationship("State", back_populates="cities")

    addresses = relationship("Address", back_populates="city")

    def __repr__(self):
        """
        Returns a string representation of the City instance.

        Returns:
            str: A string in the format <City {self.name}>.
        """
        return f"<City {self.name}>"

    def __str__(self):
        """
        Returns the name of the city.

        Returns:
            str: The name of the city.
        """
        return self.name


class Address(Base, Timestamp):
    """
    Represents an address in the database.

    Attributes:
        id (UUID): The unique identifier for the address.
        postal_code (str): The postal code of the address.
        address_line_1 (str): The first line of the address.
        address_line_2 (str): The second line of the address (optional).
        city_id (UUID): The foreign key referencing the city.
        city (relationship): The relationship to the City model.
        state_id (UUID): The foreign key referencing the state.
        state (relationship): The relationship to the State model.
        country_id (UUID): The foreign key referencing the country.
        country (relationship): The relationship to the Country model.
        shipments (relationship): The relationship to the Shipment model.
    """

    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    postal_code = Column(String(20), nullable=False, index=True)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255))

    city_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    city = relationship("City", back_populates="addresses")

    state_id = Column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    state = relationship("State", back_populates="addresses")

    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    country = relationship("Country", back_populates="addresses")

    shipments = relationship("Shipment", back_populates="address")

    def __repr__(self):
        """
        Returns a string representation of the Address instance.

        Returns:
            str: A string in the format <Address {self.address_line_1}>.
        """
        return f"<Address {self.address_line_1}>"

    def __str__(self):
        """
        Returns the first line of the address.

        Returns:
            str: The first line of the address.
        """
        return self.address_line_1


class Carrier(Base, Timestamp):
    """
    Represents a carrier in the database.

    Attributes:
        id (UUID): The unique identifier for the carrier.
        name (str): The name of the carrier.
        regex_tracking_number (str): The regular expression for the tracking number.
        shipments (relationship): The relationship to the Shipment model.
    """

    __tablename__ = "carriers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    name = Column(String(128), unique=True)
    regex_tracking_number = Column(JSONB, nullable=False)
    shipments = relationship("Shipment", back_populates="carrier")

    def __repr__(self):
        """
        Returns a string representation of the Carrier instance.

        Returns:
            str: A string in the format <Carrier {self.name}>.
        """
        return f"<Carrier {self.name}>"

    def __str__(self):
        """
        Returns the name of the carrier.

        Returns:
            str: The name of the carrier.
        """
        return self.name


class Package(Base, Timestamp):
    """
    Represents a package in the database.

    Attributes:
        id (UUID): The unique identifier for the package.
        weight (Numeric): The weight of the package.
        weight_unit (Enum): The unit of the weight (default is grams).
        length (Numeric): The length of the package.
        width (Numeric): The width of the package.
        height (Numeric): The height of the package.
        dimensions_unit (Enum): The unit of the dimensions (default is centimeters).
        shipment_id (UUID): The foreign key referencing the shipment.
        shipment (relationship): The relationship to the Shipment model.
    """

    __tablename__ = "packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    weight = Column(Numeric(10, 2), nullable=False)
    weight_unit = Column(Enum(WeightUnit), default=WeightUnit.GRAM, nullable=False)
    length = Column(Numeric(10, 2), nullable=False)
    width = Column(Numeric(10, 2), nullable=False)
    height = Column(Numeric(10, 2), nullable=False)
    dimensions_unit = Column(
        Enum(DimensionsUnit), default=DimensionsUnit.CM, nullable=False
    )

    shipment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shipment = relationship("Shipment", back_populates="packages")

    def __repr__(self):
        """
        Returns a string representation of the Package instance.

        Returns:
            str: A string in the format <Package: weight:{self.weight} {self.weight_unit}>.
        """
        return f"<Package: weight:{self.weight} {self.weight_unit}>"

    def __str__(self):
        """
        Returns the weight and weight unit of the package.

        Returns:
            str: The weight and weight unit of the package.
        """
        return f"{self.weight} {self.weight_unit}"


class Shipment(Base, Timestamp):
    """
    Represents a shipment in the database.

    Attributes:
        id (UUID): The unique identifier for the shipment.
        shipment_number (str): The shipment number, also known as the tracking number.
        shipment_date (DateTime): The date when the shipment was picked up.
        price (Numeric): The price of the shipment.
        currency (CurrencyType): The currency of the price.
        total_weight (Numeric): The total weight of the shipment.
        total_weight_unit (Enum): The unit of the total weight (default is grams).
        packages (relationship): The relationship to the Package model.
        carrier_id (UUID): The foreign key referencing the carrier.
        carrier (relationship): The relationship to the Carrier model.
        address_id (UUID): The foreign key referencing the address.
        address (relationship): The relationship to the Address model.
    """

    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=make_uuid, unique=True)
    shipment_number = Column(
        String(40), nullable=False
    )  # Shipment number, also known as the tracking number
    shipment_date = Column(
        DateTime(timezone=True), nullable=False
    )  # Date when the shipment was picked up
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(CurrencyType, nullable=False)
    total_weight = Column(Numeric(15, 2), nullable=False)
    total_weight_unit = Column(
        Enum(WeightUnit), default=WeightUnit.GRAM, nullable=False
    )

    packages = relationship("Package", back_populates="shipment")

    carrier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("carriers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    carrier = relationship("Carrier", back_populates="shipments")

    address_id = Column(
        UUID(as_uuid=True),
        ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    address = relationship("Address", back_populates="shipments")

    def __repr__(self):
        """
        Returns a string representation of the Shipment instance.

        Returns:
            str: A string in the format <Shipment {self.shipment_number}>.
        """
        return f"<Shipment {self.shipment_number}>"

    def __str__(self):
        """
        Returns the shipment number.

        Returns:
            str: The shipment number.
        """
        return self.shipment_number
