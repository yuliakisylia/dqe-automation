import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture(scope="session")
def path_to_file():
   return Path(__file__).resolve().parents[1] / "src" / "data" / "data.csv"

# Fixture to read the CSV file
@pytest.fixture(scope="session")
def csv_data(path_to_file):
   return pd.read_csv(path_to_file)

# Fixture to validate the schema of the file
@pytest.fixture(scope="session")
def validate_schema():
   def check_schema(actual_schema, expected_schema):
       assert actual_schema == expected_schema, (
           f"Schema mismatch. Expected: {expected_schema}, "
           f"Actual: {actual_schema}"
       )
   return check_schema

# Pytest hook to mark unmarked tests with a custom mark
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(items):
   for item in items:
       if not list(item.iter_markers()):
           item.add_marker(pytest.mark.unmarked)