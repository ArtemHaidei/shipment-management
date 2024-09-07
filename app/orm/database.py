from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URI = "postgresql+asyncpg://postgres:postgres@localhost:5434/senvo-dev-db"

metadata = MetaData()

engine = create_async_engine(
    DATABASE_URI,
    connect_args={
        "server_settings": {"jit": "off"},
    },
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass
