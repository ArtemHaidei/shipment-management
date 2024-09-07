import logging
import time
import json
import asyncio
import aiofiles

from uuid import UUID
from sqlalchemy import select, func

from app.orm.database import async_session
from app.orm.models import Country, State, City
from app.schemas.address import CountryIn, StateIn, CityIn


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DUMMY COUNTRIES")


async def retrieve_data_from_json(path: str | None = None):
    """
    Retrieves data from a JSON file asynchronously.

    Args:
        path (str | None): The path to the JSON file. Defaults to 'data/countries_states_cities.json'.

    Returns:
        collections.AsyncIterable: An asynchronous iterable of country data.
    """
    if not path:
        path = r"data/countries_states_cities.json"

    async with aiofiles.open(path) as file:
        content = await file.read()
        data = json.loads(content)
        for country in data:
            yield country


async def create_country(session, item: dict) -> Country:
    """
    Creates a country record in the database.

    Args:
        session: The database session.
        item (dict): The country data.

    Returns:
        Country: The created Country object.
    """
    schema = CountryIn(
        name=item["name"],
        code=item["numeric_code"],
        iso3=item["iso3"],
        iso2=item["iso2"],
    )
    country = Country(**schema.model_dump())

    session.add(country)
    await session.flush()
    return country


async def create_state(session, item: dict, country_id: UUID) -> State:
    """
    Creates a state record in the database.

    Args:
        session: The database session.
        item (dict): The state data.
        country_id (UUID): The UUID of the country.

    Returns:
        State: The created State object.
    """
    schema = StateIn(name=item["name"], country_id=country_id)
    state = State(**schema.model_dump())

    session.add(state)
    await session.flush()
    return state


async def create_countries():
    """
    Creates country, state, and city records in the database from JSON data.
    """
    async with async_session() as session:
        async with session.begin():
            # Execute a query to count the number of entries in the Country table
            result = await session.execute(select(func.count()).select_from(Country))
            count = result.scalar()

            # Check if there are any countries in the database
            if count > 0:
                logger.info("Countries already exist in the database.")
                return  # Exit the function

            count, countries_count, states_count, cities_count = 0, 0, 0, 0

            async for item in retrieve_data_from_json():
                country = await create_country(session, item)
                count += 1
                countries_count += 1
                if item.get("states"):
                    for state_item in item["states"]:
                        state = await create_state(session, state_item, country.id)
                        count += 1
                        states_count += 1

                        if state_item.get("cities"):
                            tasks = [
                                City(
                                    **CityIn(
                                        name=city_name,
                                        state_id=state.id,
                                        country_id=country.id,
                                    ).model_dump()
                                )
                                for city_name in state_item["cities"]
                            ]

                            session.add_all(tasks)
                            await session.flush()
                            # counting
                            tasks_len = len(tasks)
                            count += tasks_len
                            cities_count += tasks_len

            await session.commit()
            logger.info(f"Cities total: {cities_count}")
            logger.info(f"States total: {states_count}")
            logger.info(f"Countries total: {countries_count}")
            logger.info(f"Total records created: {count}")

        logger.info("Countries, states, and cities have been created.")


async def main():
    """
    The main function.
    """
    await create_countries()


if __name__ == "__main__":
    logger.info("Creating countries, states, and cities...")
    start = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    end = time.time()
    logger.info(f"TOTAL TIME: {end - start}")
