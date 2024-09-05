import logging
from typing import Annotated
from datetime import datetime
from fastapi import status
from fastapi import APIRouter, HTTPException, Query, Body

from app.schemas.shipment import ShipmentListOut
from app.crud.shipment import retrive_shipments_from_db, create_shipment_in_db
from app.schemas.shipment import ShipmentIn, ShipmentOut


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SHIPMENT API")

router = APIRouter(
    prefix="/shipment",
    tags=["shipment"],
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=ShipmentListOut)
async def retrive_shipments(
    start_datetime: Annotated[
        datetime | None,
        Query(title="Start date for filtering (inclusive)", example="2022-01-01"),
    ] = None,
    end_datetime: Annotated[
        datetime | None,
        Query(title="End date for filtering (inclusive)", example="2022-12-31"),
    ] = None,
    carriers: Annotated[
        list[str] | None,
        Query(
            title="List of carriers to filter by",
            min_length=2,
            max_length=128,
            example=["DHL", "FedEx"],
        ),
    ] = None,
    min_price: Annotated[
        int | None,
        Query(title="Minimum price for filtering", ge=0, le=1_000_000, example=100),
    ] = None,
    max_price: Annotated[
        int | None,
        Query(title="Maximum price for filtering", ge=0, le=1_000_000, example=1000),
    ] = None,
    page: Annotated[int, Query(title="Page number", ge=1)] = 1,
    limit: Annotated[int, Query(title="Number of items per page", ge=1, le=30)] = 10,
):
    """
    Retrieves a list of shipments from the database.

    :param start_datetime:
    :param end_datetime:
    :param carriers:
    :param min_price:
    :param max_price:
    :param page:
    :param limit:
    :return:
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The minimum price ({min_price}) cannot be greater than the maximum price ({max_price}).",
        )

    shipments, total = await retrive_shipments_from_db(
        page=page,
        limit=limit,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        carriers=carriers,
        min_price=min_price,
        max_price=max_price,
    )

    if total == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No shipments found."
        )

    return {
        "page": page,
        "next_page": page + 1 if total > page * limit else None,
        "limit": limit,
        "total": total,
        "items": len(shipments),
        "shipments": shipments,
    }


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=list[ShipmentOut])
async def create_shipment(
    shipments: Annotated[list[ShipmentIn], Body(title="List of shipments")],
):
    sipments: list[ShipmentOut] = await create_shipment_in_db(shipments)

    if not sipments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No shipments created."
        )

    return sipments
