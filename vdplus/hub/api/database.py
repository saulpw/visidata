import os

from peewee import PostgresqlDatabase

if os.getenv("VD_ENV") == "dev" or os.getenv("CI") == "true":
    db = PostgresqlDatabase(
        'vdwww',
        host = os.getenv("POSTGRES_HOST", "localhost"),
        user = os.getenv("POSTGRES_USER", os.getenv("USER")),
        password = os.getenv('POSTGRES_PASSWORD', '')
    )
else:
    db = PostgresqlDatabase(
        'vdwww',
        user = 'postgres',
        host = 'postgres-postgresql.postgres',
        password = os.getenv('POSTGRES_PASSWORD')
    )
