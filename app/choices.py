from typing import Type

from babel import Locale
from enum import Enum


class DimensionsUnit(Enum):
    """
    Enum representing units of dimension.

    Attributes:
        MM (str): Millimeter unit represented as "MM".
        CM (str): Centimeter unit represented as "CM".
        IN (str): Inch unit represented as "IN".
    """

    MM = "MM"
    CM = "CM"
    IN = "IN"


class WeightUnit(Enum):
    """
    Enum representing units of weight.

    Attributes:
        GRAM (str): Gram unit represented as "GRAM".
        KG (str): Kilogram unit represented as "KG".
        LB (str): Pound unit represented as "LB".
    """

    GRAM = "GRAM"
    KG = "KG"
    LB = "LB"


def create_currency_enum() -> Type[Enum]:
    """
    Creates an enumeration of currency codes.

    This function uses the Babel library to get a list of currency codes
    for the 'en' locale and creates an Enum with these currency codes.

    Returns:
        Enum: An enumeration of currency codes.
    """
    locale = Locale("en")
    currencies = tuple(locale.currencies)

    return Enum("CurrencyEnum", {code: code for code in currencies})


CurrencyEnum = create_currency_enum()
