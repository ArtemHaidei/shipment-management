from typing import Type

from babel import Locale
from enum import Enum


class DimensionsUnit(Enum):
    """
    Enum representing units of dimension.

    Attributes:
        MM (tuple): Millimeter unit represented as "mm".
        CM (tuple): Centimeter unit represented as "cm".
        IN (tuple): Inch unit represented as "in".
    """

    MM = "mm"
    CM = "cm"
    IN = "in"


class WeightUnit(Enum):
    """
    Enum representing units of weight.

    Attributes:
        GRAM (str): Gram unit represented as "g".
        KG (str): Kilogram unit represented as "kg".
        LB (str): Pound unit represented as "lb".
    """

    GRAM = "g"
    KG = "kg"
    LB = "lb"


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
