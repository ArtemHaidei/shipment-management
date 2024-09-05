FROM postgres:16-alpine

ENV POSTGRES_DB=senvo-dev-db \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres \
    POSTGRES_PORT=5432

EXPOSE 54324

VOLUME ["/var/lib/postgresql/data"]