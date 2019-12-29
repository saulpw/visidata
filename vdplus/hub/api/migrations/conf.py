import os

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "")
host = os.getenv("POSTGRES_HOST", "localhost")

DATABASE = "postgres://%s:%s@%s/vdwww" % (user, password, host)
