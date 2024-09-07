from fastapi import HTTPException


class CountryNotFoundError(HTTPException):
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
    def __init__(self, city_name: str, country_name: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "address", "city"],
                "msg": f"City '{city_name}' does not belong to country '{country_name}'.",
                "type": "value_error",
            },
        )
