from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.orm.database import async_session
from app.orm.models import Shipment, Carrier, Address, Package
from app.schemas.shipment import ShipmentIn, ShipmentOut
from app.schemas.address import AddressId


async def shipments_post_request(stmt) -> list[Shipment]:
    """
    Executes a SQL statement to retrieve shipments from the database and returns the results.

    Args:
        stmt: The SQL statement to execute.

    Returns:
        list: A list of unique Shipment objects.
    """
    async with async_session() as session, session.begin():
        stmt = stmt.order_by(Shipment.created.desc())
        stmt = stmt.options(
            joinedload(Shipment.address).joinedload(Address.city),
            joinedload(Shipment.address).joinedload(Address.state),
            joinedload(Shipment.address).joinedload(Address.country),
            joinedload(Shipment.packages),
            joinedload(Shipment.carrier),
        )

        results = await session.execute(stmt)
        return results.scalars().unique().all()


async def shipments_get_request(stmt, total_stmt) -> tuple[list[Shipment], int]:
    """
    Executes SQL statements to retrieve shipments and their total count from the database.

    Args:
        stmt: The SQL statement to execute for retrieving shipments.
        total_stmt: The SQL statement to execute for retrieving the total count of shipments.

    Returns:
        tuple: A tuple containing a list of unique Shipment objects and the total count of shipments.
    """
    async with async_session() as session, session.begin():
        total_result = await session.execute(total_stmt)

        total = total_result.scalar()

        if total == 0:
            return [], 0

        stmt = stmt.order_by(Shipment.created.desc())
        stmt = stmt.options(
            joinedload(Shipment.address).joinedload(Address.city),
            joinedload(Shipment.address).joinedload(Address.state),
            joinedload(Shipment.address).joinedload(Address.country),
            joinedload(Shipment.packages),
            joinedload(Shipment.carrier),
        )
        # check the total number of records acording to the filters
        results = await session.execute(stmt)
        shipments = results.scalars().unique().all()

        return shipments, total


async def retrive_shipments_from_db(
    **kwargs,
) -> tuple[list[Shipment], int] | tuple[list, Any]:
    """
    Retrieves shipments from the database based on provided filters.

    Args:
        **kwargs: Arbitrary keyword arguments for filtering shipments.

    Returns:
        tuple: A tuple containing a list of Shipment objects and the total count of shipments.
    """
    limit = kwargs.get("limit", 10)
    page = kwargs.get("page", 1)
    offset = (page - 1) * limit

    stmt = select(Shipment).offset(offset).limit(limit)
    total_stmt = select(func.count()).select_from(Shipment)

    if kwargs.get("carriers"):
        stmt = stmt.join(Carrier).filter(Carrier.name.in_(kwargs["carriers"]))
        total_stmt = total_stmt.join(Carrier).filter(
            Carrier.name.in_(kwargs["carriers"])
        )

    if kwargs.get("start_datetime"):
        stmt = stmt.filter(Shipment.shipment_date >= kwargs["start_datetime"])
        total_stmt = total_stmt.filter(
            Shipment.shipment_date >= kwargs["start_datetime"]
        )

    if kwargs.get("end_datetime"):
        stmt = stmt.filter(Shipment.shipment_date <= kwargs["end_datetime"])
        total_stmt = total_stmt.filter(Shipment.shipment_date <= kwargs["end_datetime"])

    if kwargs.get("min_price"):
        stmt = stmt.filter(Shipment.price >= kwargs["min_price"])
        total_stmt = total_stmt.filter(Shipment.price >= kwargs["min_price"])

    if kwargs.get("max_price"):
        stmt = stmt.filter(Shipment.price <= kwargs["max_price"])
        total_stmt = total_stmt.filter(Shipment.price <= kwargs["max_price"])

    return await shipments_get_request(stmt, total_stmt)


def create_packages(shipment: ShipmentIn, shipment_id: UUID) -> list[Package]:
    """
    Creates Package objects for a given shipment.

    Args:
        shipment (ShipmentIn): The shipment data.
        shipment_id (UUID): The ID of the shipment.

    Returns:
        list: A list of Package objects.
    """
    return [
        Package(
            **package.model_dump(),
            shipment_id=shipment_id,
        )
        for package in shipment.packages
    ]


async def create_shipment_in_db(
    shipments: tuple[AddressId], carriers: tuple[Carrier]
) -> tuple[list[Shipment], int]:
    """
    Creates shipments in the database.

    Args:
        shipments (tuple[AddressId]): A tuple containing AddressId objects representing the shipments.
        carriers (tuple[Carrier]): A tuple containing Carrier objects.

    Returns:
        tuple[list[Shipment], int]: A tuple containing a list of created Shipment objects and the total number of shipments created.
    """

    shipments_id: list[ShipmentOut] = []
    async with async_session() as session, session.begin():
        for item in shipments:
            address = Address(
                **item.shipment.address.model_dump(
                    exclude={"country", "state", "city"}
                ),
                **item.model_dump(exclude={"shipment"}),
            )
            session.add(address)
            await session.flush()

            carrier = next(
                (x for x in carriers if x.name == item.shipment.carrier), None
            )
            if not carrier:
                raise ValueError(
                    f"No carrier found with the name {item.shipment.carrier}"
                )

            shipment_instance = Shipment(
                **item.shipment.model_dump(exclude={"address", "packages", "carrier"}),
                carrier_id=carrier.id,
                address_id=address.id,
            )
            session.add(shipment_instance)
            await session.flush()

            package_instances = create_packages(item.shipment, shipment_instance.id)
            session.add_all(package_instances)

            await session.flush()

            shipments_id.append(shipment_instance.id)

        await session.commit()

    stmt = select(Shipment).where(Shipment.id.in_(shipments_id)).limit(100)
    return await shipments_post_request(stmt), len(shipments_id)
