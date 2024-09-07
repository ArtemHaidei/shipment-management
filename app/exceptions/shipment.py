from fastapi import HTTPException


class CarrierNotFoundError(HTTPException):
    """
    Exception raised when a carrier is not found.

    Args:
        carrier_name (str): The name of the carrier that was not found.
    """

    def __init__(self, carrier_name: str):
        super().__init__(
            status_code=400,
            detail={
                {
                    "loc": ["body", "carrier"],
                    "msg": f"Carrier '{carrier_name}' does not exist.",
                    "type": "value_error",
                }
            },
        )


class ShipmentNumberMismatchError(HTTPException):
    """
    Exception raised when a shipment number does not match any pattern for a carrier.

    Args:
        carrier_name (str): The name of the carrier.
        shipment_number (str): The shipment number that does not match any pattern.
    """

    def __init__(self, carrier_name: str, shipment_number: str):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "shipment_number"],
                "msg": f"Shipment number '{shipment_number}' does not match any pattern for carrier '{carrier_name}'.",
                "type": "value_error",
            },
        )


class ShipmentDateError(HTTPException):
    """
    Exception raised when the shipment pickup date is in the future.
    """

    def __init__(self):
        super().__init__(
            status_code=400,
            detail={
                "loc": ["body", "pickup_date"],
                "msg": "The date when the shipment was picked up cannot be in the future.",
                "type": "value_error",
            },
        )
