#!/bin/bash

# Load environment variables from .env file
set -a
source .env
set +a

# Set the Flask environment to testing
export FLASK_ENV=testing

# Print the database connection string for debugging (without showing the password)
echo "Database connection string: ${TEST_DATABASE_URL//:*@/:********@}"

# Ensure the test database exists
psql -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_TEST_DB;" || true

# Run the specific test with verbose output
python -m pytest tests/api/test_batch_api.py::test_start_batches -v

# Note: We're not dropping the test database after the test run
# as it's a shared resource defined in the .env file
