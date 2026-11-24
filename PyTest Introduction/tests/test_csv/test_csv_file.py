import pytest
import pandas as pd

def test_file_not_empty(csv_data):
   assert not csv_data.empty, "CSV file is empty"

@pytest.mark.validate_csv
@pytest.mark.xfail(reason="Duplicate rows in CSV")
def test_duplicates(csv_data):
   duplicates = csv_data[csv_data.duplicated(keep=False)]
   assert duplicates.empty, f"Duplicate rows found:\n{duplicates}"

@pytest.mark.validate_csv
def test_validate_schema(csv_data, validate_schema):
   expected_schema = ["id", "name", "age", "email", "is_active"]
   actual_schema = csv_data.columns.tolist()
   validate_schema(actual_schema, expected_schema)

@pytest.mark.validate_csv
@pytest.mark.skip(reason="Skipped according to homework requirements")
def test_age_column_valid(csv_data):
   age = pd.to_numeric(csv_data["age"], errors="coerce")
   valid_age = age.notna() & age.between(0, 100)
   invalid_rows = csv_data[~valid_age.fillna(False)]
   assert invalid_rows.empty, f"Invalid age values:\n{invalid_rows}"

@pytest.mark.validate_csv
def test_email_column_valid(csv_data):
   pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
   valid_email = csv_data["email"].astype("string").str.fullmatch(
       pattern, na=False
   )
   invalid_rows = csv_data[~valid_email]
   assert invalid_rows.empty, f"Invalid emails found:\n{invalid_rows}"

@pytest.mark.parametrize("id, is_active", [
   (1, False),
   (2, True)
])
def test_active_players(csv_data, id, is_active):
   player = csv_data[csv_data["id"] == id]
   assert len(player) == 1, f"Expected one record for ID {id}"
   actual_status = player["is_active"].iloc[0]
   assert actual_status == is_active, (
       f"ID {id}: Expected {is_active}, actual {actual_status}"
   )

def test_active_player(csv_data):
   player = csv_data[csv_data["id"] == 2]
   assert len(player) == 1, "Expected one record for ID 2"
   actual_status = player["is_active"].iloc[0]
   assert actual_status == True, (
       f"ID 2: Expected True, actual {actual_status}"
   )