import os

from peewee import PostgresqlDatabase

db = PostgresqlDatabase(
    'vdwww',
    host = os.getenv("POSTGRES_HOST", "localhost"),
    user = os.getenv("POSTGRES_USER", os.getenv("USER")),
    password = os.getenv('POSTGRES_PASSWORD', '')
)
