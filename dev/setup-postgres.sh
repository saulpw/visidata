#!/usr/bin/env bash
# Set up local postgres database for VisiData testing  #2203
# Usage: dev/setup-postgres.sh
# Requires: postgresql installed and running

set -e

DB=vdtest

if psql -d $DB -c "SELECT 1" > /dev/null 2>&1; then
    echo "dropping existing $DB database"
    dropdb $DB
fi

echo "creating $DB database"
createdb $DB

echo "importing benchmark table"
psql -d $DB -c "CREATE TABLE benchmark (
    date TEXT,
    customer TEXT,
    sku TEXT,
    item TEXT,
    quantity INT,
    unit TEXT,
    paid TEXT,
    PRIMARY KEY (date, customer, sku)
)"
psql -d $DB -c "\copy benchmark FROM 'sample_data/benchmark.csv' CSV HEADER"

echo "verifying"
n=$(psql -d $DB -tAc "SELECT count(*) FROM benchmark")
echo "$n rows in benchmark table"

echo "setup complete: run tests with dev/test-all.sh tests/test-postgres.sh"
