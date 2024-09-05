#!/bin/bash

DB_NAME="senvo-test-db"
DB_USER="postgres"
DB_PASS="postgres"
DB_HOST="localhost"
DB_PORT="5434"

database_exists() {
  PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1
}

create_database() {
  echo "Creating database '$DB_NAME'"
  PGPASSWORD=$DB_PASS createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
}

if database_exists; then
  echo "Database '$DB_NAME' already exists"
else
  create_database
fi