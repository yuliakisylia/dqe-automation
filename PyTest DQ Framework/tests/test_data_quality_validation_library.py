import pandas as pd
import pytest

from src.data_quality.data_quality_validation_library import DataQualityLibrary


@pytest.fixture
def data_quality_library():
    return DataQualityLibrary()


def test_completeness_allows_listed_partition_column_and_preserves_duplicates(
    data_quality_library,
):
    expected = pd.DataFrame(
        {"facility_type": ["Clinic", "Clinic"], "sum_treatment_cost": [25, 25]}
    )
    actual = expected.assign(facility_type_partition="Clinic")

    data_quality_library.check_data_completeness(
        expected,
        actual,
        allowed_partition_columns=["facility_type_partition"],
    )


def test_completeness_rejects_partition_column_without_allowlist(
    data_quality_library,
):
    expected = pd.DataFrame({"value": [1]})
    actual = expected.assign(partition_date=["2026-11"])

    with pytest.raises(
        AssertionError, match="unexpected columns: \\['partition_date'\\]"
    ):
        data_quality_library.check_data_completeness(expected, actual)


def test_completeness_rejects_unlisted_extra_column(data_quality_library):
    expected = pd.DataFrame({"value": [1]})
    actual = expected.assign(partition_date=["2026-11"], unexpected=["x"])

    with pytest.raises(AssertionError, match="unexpected columns: \\['unexpected'\\]"):
        data_quality_library.check_data_completeness(
            expected, actual, allowed_partition_columns=["partition_date"]
        )


def test_completeness_rejects_missing_business_column(data_quality_library):
    expected = pd.DataFrame({"facility_type": ["Clinic"], "value": [1]})
    actual = pd.DataFrame(
        {"facility_type": ["Clinic"], "facility_type_partition": ["Clinic"]}
    )

    with pytest.raises(AssertionError, match="Missing expected columns: \\['value'\\]"):
        data_quality_library.check_data_completeness(
            expected,
            actual,
            allowed_partition_columns=["facility_type_partition"],
        )


@pytest.mark.parametrize(
    "actual_rows",
    [
        [("A", 10), ("B", 20)],
        [("A", 10), ("A", 10)],
        [("A", 10), ("A", 10), ("B", 20), ("C", 30)],
        [("A", 10), ("A", 10), ("B", 999)],
    ],
    ids=[
        "missing-duplicate-occurrence",
        "missing-record",
        "extra-record",
        "incorrect-value",
    ],
)
def test_completeness_detects_business_row_mismatches(
    data_quality_library, actual_rows
):
    expected = pd.DataFrame(
        [("A", 10), ("A", 10), ("B", 20)], columns=["name", "value"]
    )
    actual = pd.DataFrame(actual_rows, columns=["name", "value"])
    actual["partition_date"] = "2026-11"

    with pytest.raises(
        AssertionError,
        match="Data completeness failed: expected and actual rows differ",
    ):
        data_quality_library.check_data_completeness(
            expected, actual, allowed_partition_columns=["partition_date"]
        )


def test_partition_column_consistency_accepts_derived_values(data_quality_library):
    actual = pd.DataFrame(
        {
            "visit_date": pd.to_datetime(["2026-11-02", "2026-12-03"]),
            "partition_date": ["2026-11", "2026-12"],
        }
    )
    expected_partition = (
        actual["visit_date"].dt.to_period("M").astype(str)
    )

    data_quality_library.check_partition_column_consistency(
        actual, "partition_date", expected_partition
    )


def test_partition_column_consistency_detects_incorrect_value(data_quality_library):
    actual = pd.DataFrame(
        {"visit_date": pd.to_datetime(["2026-11-02"]), "partition_date": ["2026-10"]}
    )
    expected_partition = actual["visit_date"].dt.to_period("M").astype(str)

    with pytest.raises(AssertionError, match="does not match its business values"):
        data_quality_library.check_partition_column_consistency(
            actual, "partition_date", expected_partition
        )
