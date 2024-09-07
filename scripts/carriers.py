import logging
import asyncio

from app.orm.models import Carrier
from app.schemas.shipment import CarrierIn

from app.orm.database import async_session


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example regex patterns for DHL Express, UPS, and FedEx with multiple types
carrier_data = [
    {
        "name": "dhl-express",
        "regex_tracking_number": {
            "standard": r"^\d{10}$",  # Standard DHL tracking numbers (10 digits)
            "express": r"^[A-Za-z0-9\-]{13,20}$",  # Alphanumeric DHL express format
        },
    },
    {
        "name": "ups",
        "regex_tracking_number": {
            "standard": r"^1Z[A-Za-z0-9]{16}$",  # Standard UPS tracking numbers
            "freight": r"^\d{9}$",  # UPS Freight 9-digit numbers
            "international": r"^\d{18}$",  # 18-digit UPS international tracking
        },
    },
    {
        "name": "fedex",
        "regex_tracking_number": {
            "standard": r"^\d{12,14}$",  # Standard FedEx (12-14 digits)
            "ground": r"^\d{15,20}$",  # FedEx Ground (15-20 digits)
            "smartpost": r"^[0-9]{20}$",  # SmartPost (20 digits)
        },
    },
]


async def create_carrier() -> None:
    """
    Creates carrier records in the database.
    """
    async with async_session() as session:
        async with session.begin():
            for item in carrier_data:
                schema = CarrierIn(
                    name=item["name"],
                    regex_tracking_number=item["regex_tracking_number"],
                )
                carrier = Carrier(**schema.model_dump())
                session.add(carrier)
            await session.commit()


async def main():
    """
    The main function.
    """
    await create_carrier()


if __name__ == "__main__":
    logging.info("Creating carrier records in the database...")
    asyncio.run(main())
    logging.info("Carrier records have been created.")
