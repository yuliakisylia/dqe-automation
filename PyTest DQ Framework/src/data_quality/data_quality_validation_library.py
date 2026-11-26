from collections import Counter
from typing import Hashable, List, Optional

import pandas as pd


class DataQualityLibrary:
    """Reusable data quality assertions for pandas DataFrames."""

    @staticmethod
    def check_dataset_is_not_empty(df: pd.DataFrame) -> None:
        assert not df.empty, "Dataset is empty."

    @staticmethod
    def check_data_completeness(
        df_expected: pd.DataFrame, df_actual: pd.DataFrame
    ) -> None:
        if (
            len(df_expected.columns) != len(df_actual.columns)
            or set(df_expected.columns) != set(df_actual.columns)
        ):
            raise AssertionError(
                "Data completeness failed: column names differ. "
                f"Expected: {list(df_expected.columns)}; "
                f"actual: {list(df_actual.columns)}."
            )

        expected = df_expected.loc[:, list(df_expected.columns)].copy()
        actual = df_actual.loc[:, list(df_expected.columns)].copy()

        for column in expected.columns:
            if (
                pd.api.types.is_datetime64_any_dtype(expected[column])
                or pd.api.types.is_datetime64_any_dtype(actual[column])
            ):
                expected[column] = pd.to_datetime(expected[column])
                actual[column] = pd.to_datetime(actual[column])

        def sort_rows(df: pd.DataFrame) -> pd.DataFrame:
            row_order = (
                pd.util.hash_pandas_object(df, index=False)
                .to_numpy()
                .argsort(kind="stable")
            )
            return df.iloc[row_order].reset_index(drop=True)

        expected_sorted = sort_rows(expected)
        actual_sorted = sort_rows(actual)
        try:
            pd.testing.assert_frame_equal(
                expected_sorted,
                actual_sorted,
                check_dtype=False,
                check_exact=True,
            )
        except AssertionError as error:
            expected_hashes = pd.util.hash_pandas_object(
                expected, index=False
            ).tolist()
            actual_hashes = pd.util.hash_pandas_object(
                actual, index=False
            ).tolist()

            def rows_not_in_other(
                df: pd.DataFrame,
                hashes: List[Hashable],
                other_hashes: List[Hashable],
            ) -> pd.DataFrame:
                available_hashes = Counter(other_hashes)
                unmatched_indices = []
                for index, row_hash in enumerate(hashes):
                    if available_hashes[row_hash]:
                        available_hashes[row_hash] -= 1
                    else:
                        unmatched_indices.append(index)
                return df.iloc[unmatched_indices[:10]]

            expected_mismatches = rows_not_in_other(
                expected, expected_hashes, actual_hashes
            )
            actual_mismatches = rows_not_in_other(
                actual, actual_hashes, expected_hashes
            )
            raise AssertionError(
                "Data completeness failed: expected and actual rows differ "
                "(row order is ignored).\n"
                f"Expected-only rows:\n{expected_mismatches}\n"
                f"Actual-only rows:\n{actual_mismatches}\n"
                f"Comparison details: {error}"
            ) from error

    @staticmethod
    def check_count(df_expected: pd.DataFrame, df_actual: pd.DataFrame) -> None:
        expected_count = len(df_expected)
        actual_count = len(df_actual)
        assert expected_count == actual_count, (
            "Row counts differ: "
            f"expected {expected_count}, actual {actual_count}."
        )

    @staticmethod
    def check_duplicates(
        df: pd.DataFrame, column_names: Optional[List[str]] = None
    ) -> None:
        if column_names is not None:
            DataQualityLibrary._validate_columns(df, column_names)

        duplicate_mask = df.duplicated(subset=column_names, keep=False)
        duplicates = df.loc[duplicate_mask]
        assert duplicates.empty, (
            f"Found {len(duplicates)} duplicate rows using "
            f"{'all columns' if column_names is None else column_names}. "
            f"Sample:\n{duplicates.head(10)}"
        )

    @staticmethod
    def check_not_null_values(
        df: pd.DataFrame, column_names: List[str]
    ) -> None:
        DataQualityLibrary._validate_columns(df, column_names)
        null_counts = df[column_names].isna().sum()
        columns_with_nulls = null_counts[null_counts > 0]
        assert columns_with_nulls.empty, (
            "Null values found: "
            + ", ".join(
                f"{column} ({count})"
                for column, count in columns_with_nulls.items()
            )
        )

    @staticmethod
    def _validate_columns(df: pd.DataFrame, column_names: List[str]) -> None:
        if not column_names:
            raise ValueError("At least one column name must be provided.")
        missing_columns = [name for name in column_names if name not in df.columns]
        if missing_columns:
            raise ValueError(f"Columns not found in DataFrame: {missing_columns}")
