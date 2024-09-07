import logging
import asyncio
from typing import Annotated
from datetime import datetime
from fastapi import status
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from app.schemas.shipment import ShipmentListOut
from app.crud.shipment import retrive_shipments_from_db, create_shipment_in_db
from app.schemas.shipment import ShipmentIn, ShipmentPostOut

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
            min_length=1,
            max_length=128,
            example=["dhl-express", "ups", "fedex"],
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
    limit: Annotated[int, Query(title="Number of items per page", ge=1, le=100)] = 10,
):
    """
    Retrieves a list of shipments from the database.

    ### - query param `start_datetime`
    ### - query param `end_datetime`
    ### - query param `carriers`
    ### - query param `min_price`
    ### - query param `max_price`
    ### - query param `page`
    ### - query param `limit`
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

    if len(shipments) == 0:
        if page > 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No more shipments found."
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No shipments found."
        )

    return {
        "page": page,
        "next_page": page + 1 if total > page * limit else None,
        "last_page": total // limit + 1,
        "limit": limit,
        "total": total,
        "items": len(shipments),
        "records": shipments,
    }


# response_model=list[ShipmentOut]
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ShipmentPostOut)
async def create_shipment(
    shipments: Annotated[
        list[ShipmentIn], Body(title="List of shipments", min_length=1, max_length=100)
    ],
):
    """
    Creates new shipment records in the database.

    Args:
        shipments (list[ShipmentIn]): A list of shipment data to be created. The list must contain between 1 and 100 items.

    Returns:
        JSONResponse: A JSON response containing the number of created records and a message indicating the result.
    """
    # Validate the carriers for each shipment
    cariers = await asyncio.gather(
        *(shipment.validate_carrier() for shipment in shipments)
    )
    # Check if the country, state, and city exist for each shipment's address
    result = await asyncio.gather(
        *(
            shipment.address.check_if_country_state_city_exists(shipment)
            for shipment in shipments
        )
    )
    # Create the shipments in the database
    result_lst, records_recieved_len = await create_shipment_in_db(result, cariers)
    created_records = len(result_lst)

    # If not all records were created, return a partial success response
    if created_records != records_recieved_len:
        return JSONResponse(
            content={
                "created": created_records,
                "message": "Some records were not created",
            },
            status_code=status.HTTP_200_OK,
        )

    return {
        "created": created_records,
        "records": result_lst,
        "message": "All records created",
    }
