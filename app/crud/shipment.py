from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.orm.database import async_session
from app.orm.models import Shipment, Carrier, Address, Package
from app.schemas.shipment import ShipmentIn, ShipmentOut
from app.schemas.address import AddressId


async def shipments_post_request(stmt):
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


async def shipments_get_request(stmt, total_stmt):
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
