"""init db

Revision ID: b220fb5fbe0f
Revises:
Create Date: 2024-09-06 07:00:02.217114

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b220fb5fbe0f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "carriers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column(
            "regex_tracking_number",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "countries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("iso2", sa.String(length=2), nullable=False),
        sa.Column("iso3", sa.String(length=3), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "states",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_states_country_id"), "states", ["country_id"], unique=False
    )
    op.create_index(op.f("ix_states_name"), "states", ["name"], unique=False)
    op.create_table(
        "cities",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("country_id", sa.UUID(), nullable=True),
        sa.Column("state_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_cities_name"), "cities", ["name"], unique=False)
    op.create_index(op.f("ix_cities_state_id"), "cities", ["state_id"], unique=False)
    op.create_table(
        "addresses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("address_line_1", sa.String(length=255), nullable=False),
        sa.Column("address_line_2", sa.String(length=255), nullable=True),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("state_id", sa.UUID(), nullable=False),
        sa.Column("country_id", sa.UUID(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["country_id"], ["countries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_addresses_city_id"), "addresses", ["city_id"], unique=False
    )
    op.create_index(
        op.f("ix_addresses_country_id"), "addresses", ["country_id"], unique=False
    )
    op.create_index(
        op.f("ix_addresses_postal_code"), "addresses", ["postal_code"], unique=False
    )
    op.create_index(
        op.f("ix_addresses_state_id"), "addresses", ["state_id"], unique=False
    )
    op.create_table(
        "shipments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("shipment_number", sa.String(length=40), nullable=False),
        sa.Column("shipment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "currency",
            sqlalchemy_utils.types.currency.CurrencyType(length=3),
            nullable=False,
        ),
        sa.Column("total_weight", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "total_weight_unit",
            sa.Enum("GRAM", "KG", "LB", name="weightunit"),
            nullable=False,
        ),
        sa.Column("carrier_id", sa.UUID(), nullable=False),
        sa.Column("address_id", sa.UUID(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["address_id"], ["addresses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["carrier_id"], ["carriers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_shipments_address_id"), "shipments", ["address_id"], unique=False
    )
    op.create_index(
        op.f("ix_shipments_carrier_id"), "shipments", ["carrier_id"], unique=False
    )
    op.create_table(
        "packages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("weight", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "weight_unit",
            sa.Enum("GRAM", "KG", "LB", name="weightunit"),
            nullable=False,
        ),
        sa.Column("length", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("width", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("height", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "dimensions_unit",
            sa.Enum("MM", "CM", "IN", name="dimensionsunit"),
            nullable=False,
        ),
        sa.Column("shipment_id", sa.UUID(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_packages_shipment_id"), "packages", ["shipment_id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_packages_shipment_id"), table_name="packages")
    op.drop_table("packages")
    op.drop_index(op.f("ix_shipments_carrier_id"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_address_id"), table_name="shipments")
    op.drop_table("shipments")
    op.drop_index(op.f("ix_addresses_state_id"), table_name="addresses")
    op.drop_index(op.f("ix_addresses_postal_code"), table_name="addresses")
    op.drop_index(op.f("ix_addresses_country_id"), table_name="addresses")
    op.drop_index(op.f("ix_addresses_city_id"), table_name="addresses")
    op.drop_table("addresses")
    op.drop_index(op.f("ix_cities_state_id"), table_name="cities")
    op.drop_index(op.f("ix_cities_name"), table_name="cities")
    op.drop_table("cities")
    op.drop_index(op.f("ix_states_name"), table_name="states")
    op.drop_index(op.f("ix_states_country_id"), table_name="states")
    op.drop_table("states")
    op.drop_table("countries")
    op.drop_table("carriers")
    # ### end Alembic commands ###
