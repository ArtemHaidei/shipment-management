from fastapi import HTTPException


class CountryNotFoundError(HTTPException):
    """
    Exception raised when a country is not found.

    Args:
        country_name (str): The name of the country that was not found.
    """

    def __init__(self, country_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "country"],
                "msg": f"Country '{country_name}' does not exist.",
                "type": "value_error",
            },
        )


class StateNotFoundError(HTTPException):
    """
    Exception raised when a state is not found.

    Args:
        state_name (str): The name of the state that was not found.
    """

    def __init__(self, state_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "state"],
                "msg": f"State '{state_name}' does not exist.",
                "type": "value_error",
            },
        )


class CityNotFoundError(HTTPException):
    """
    Exception raised when a city is not found.

    Args:
        city_name (str): The name of the city that was not found.
    """

    def __init__(self, city_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "city"],
                "msg": f"City '{city_name}' does not exist.",
                "type": "value_error",
            },
        )


class StateCountryMismatchError(HTTPException):
    """
    Exception raised when a state does not belong to a specified country.

    Args:
        state_name (str): The name of the state.
        country_name (str): The name of the country.
    """

    def __init__(self, state_name: str, country_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "state"],
                "msg": f"State '{state_name}' does not belong to country '{country_name}'.",
                "type": "value_error",
            },
        )


class CityStateMismatchError(HTTPException):
    """
    Exception raised when a city does not belong to a specified state.

    Args:
        city_name (str): The name of the city.
        state_name (str): The name of the state.
    """

    def __init__(self, city_name: str, state_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "city"],
                "msg": f"City '{city_name}' does not belong to state '{state_name}'.",
                "type": "value_error",
            },
        )


class CityCountryMismatchError(HTTPException):
    """
    Exception raised when a city does not belong to a specified country.

    Args:
        city_name (str): The name of the city.
        country_name (str): The name of the country.
    """

    def __init__(self, city_name: str, country_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "city"],
                "msg": f"City '{city_name}' does not belong to country '{country_name}'.",
                "type": "value_error",
            },
        )


class CountryParametrError(HTTPException):
    """
    Exception raised when no parameters for a country are provided.
    """

    def __init__(self):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "country"],
                "msg": "At least one parameter for Country must be provided.",
                "param": ["name", "iso3", "iso2", "code"],
                "type": "value_error",
            },
        )
