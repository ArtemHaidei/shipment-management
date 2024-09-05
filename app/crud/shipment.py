from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.orm.database import async_session
from app.orm.models import Shipment, Carrier, Address, Package
from app.schemas.shipment import ShipmentIn, ShipmentOutBase, ShipmentOut


async def retrive_shipments_from_db(
    **kwargs,
) -> tuple[list[Shipment], int] | tuple[list, Any]:
    limit = kwargs.get("limit", 10)
    page = kwargs.get("page", 1)
    offset = (page - 1) * limit

    async with async_session() as session:
        async with session.begin():
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
                total_stmt = total_stmt.filter(
                    Shipment.shipment_date <= kwargs["end_datetime"]
                )

            if kwargs.get("min_price"):
                stmt = stmt.filter(Shipment.price >= kwargs["min_price"])
                total_stmt = total_stmt.filter(Shipment.price >= kwargs["min_price"])

            if kwargs.get("max_price"):
                stmt = stmt.filter(Shipment.price <= kwargs["max_price"])
                total_stmt = total_stmt.filter(Shipment.price <= kwargs["max_price"])

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
            )
            # check the total number of records acording to the filters
            results = await session.execute(stmt)
            shipments = results.scalars().all()

            return shipments, total


def create_packages(shipment: ShipmentIn, shipment_id: UUID) -> list[Package]:
    return [
        Package(
            **package.model_dump(),
            shipment_id=shipment_id,
        )
        for package in shipment.packages
    ]


def parse_shipments_out(shipments: list[Shipment]) -> list[ShipmentOut]:
    return [
        ShipmentOut.out(
            ShipmentOutBase.model_validate(shipment),
        )
        for shipment in shipments
    ]


async def create_shipment_in_db(shipments: list[ShipmentIn]) -> list[ShipmentOut]:
    async with async_session() as session:
        async with session.begin():
            shipments_instances: list[Shipment] = []

            for shipment in shipments:
                address = Address(
                    **shipment.address.model_dump(exclude={"country", "state", "city"})
                )
                session.add(address)
                session.flush()

                shipment_instance = Shipment(
                    **shipment.model_dump(exclude={"address", "packages", "carrier"}),
                    address_id=address.id,
                )
                session.add(shipment_instance)
                session.flush()

                package_instances = create_packages(shipment, shipment_instance.id)
                session.add_all(package_instances)

                shipments_instances.append(shipment_instance)
                shipment_instance.packages = package_instances

            await session.commit()
            await session.refresh(shipment_instance)
            return parse_shipments_out(shipments_instances)
