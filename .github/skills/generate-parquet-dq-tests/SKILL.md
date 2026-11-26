---
name: generate-parquet-dq-tests
description: >-
  Generates one mapping-based PyTest DQ module for a requested Parquet dataset
  when the PyTest DQ Framework is available. It must not change framework,
  Jenkins, or conftest code, or derive expected results from ETL SQL.
disable-model-invocation: true
---

# Generate Parquet DQ tests

Complete this skill as **Step 2** of the PyTest DQ assignment. Read first:

- `PyTest DQ Framework/docs/test-automation-strategy.md` — **§5 Skill contract**, **§6 Test design standard**
- `PyTest DQ Framework/docs/dq-framework-design.md` — framework APIs, fixtures, and configuration
- `docs/parquet-aggregated-data-mapping.md` — mapped dataset definitions and expected business logic

The mapping is the source of truth for expected results. If a summary or pipeline implementation disagrees with the mapping, follow the mapping. Never copy or adapt expected SQL from `data_dev/`.

## When this skill applies

Use this skill only when the user explicitly invokes it to create or update a PyTest DQ module for one mapped Parquet dataset. The framework must already provide the documented PostgreSQL connector, Parquet reader, DQ library, fixtures, and registered markers.

Create or update only the requested dataset module under `PyTest DQ Framework/tests/dq checks/parquet_files/`. Do not create or edit framework code, `conftest.py`, `pytest.ini`, requirements, Jenkins files, mapping documents, or this skill. If the user also requests those changes, handle them only as a separate, explicit task—not as part of this skill.

Do not proceed with dataset tests if the mapping is missing, does not identify the required columns or grain, or is ambiguous about joins or transformations. Ask the user to clarify the mapping instead of guessing or consulting ETL code. If author or requirement metadata is missing, ask for it or retain clear placeholders and identify them in your response.

## Inputs you must have

- One dataset name, matching its folder under `/parquet_data/`.
- The corresponding mapping entry in `docs/parquet-aggregated-data-mapping.md`, including output columns, grain, measures, join path, and any explicitly stated filters or transformations.
- The explicitly identified technical partition column names that may appear in the reader result, if any. Get these from the user or a maintained dataset contract; do not infer them from ETL code or generated Parquet output.
- Author and requirement identifier for the module header, or permission to leave those fields as placeholders.

Use the mapping as the only source for expected SQL. Do not use `data_dev/`, pipeline or parquet-loader SQL, generated Parquet output, previews, or test results to infer or adjust expected results.

## Hard rules

1. Generate one module named `test_<dataset_name>.py` in `PyTest DQ Framework/tests/dq checks/parquet_files/`. Use the dataset folder's exact snake_case name.
2. PostgreSQL is the source and expected result: `source_data` uses `db_connection.get_data_sql(source_query)`. Parquet is the target and actual result: `target_data` uses `parquet_reader.process('/parquet_data/<dataset_name>', include_subfolders=True)`. Never swap these fixtures.
3. Derive expected SQL exclusively from the requested mapping. Include only its joins, grain, measures, formatting, rounding, date granularity, and filters. Do not add pipeline-only `UNION`, `WHERE`, `CASE`, or sign adjustments.
4. Keep this skill dataset-agnostic. Do not include concrete expected SQL for any named dataset. Alias every selected output to the mapped Parquet column name.
5. Tests must call the reusable methods in `src/data_quality/data_quality_validation_library.py`. Do not implement replacement pandas comparisons or use empty/trivial assertions.
6. Include all five checks: non-empty smoke, completeness, count, uniqueness, and not-null. Uniqueness must check the mapped grain columns—not merely all columns. The not-null list must include every mapped output column.
7. Mark every test with `parquet_data` and the requested dataset-specific marker. Mark only the non-empty test with `smoke`. Do not use the `example` marker.
8. Pass only explicitly identified technical partition columns to `allowed_partition_columns` (omit the argument or pass an empty list when there are none). Missing mapped columns and any unlisted extra columns must still fail completeness.
9. If partition columns are present and their derivation from business columns is documented, validate that relationship separately through the reusable DQ library.
10. Never compare the target to itself or alter the mapping-derived expected result to make a test pass. A discrepancy is evidence to investigate in the transformation, not a reason to weaken validation.
11. Do not modify framework files unless the user separately and explicitly requests a framework change.

## Workflow

1. Read the requested dataset's mapping entry and record its target column names, grain, measures, joins, and any explicit filters or formatting.
2. Confirm that the mapping fully specifies the expected result. If not, stop and ask for clarification; do not inspect pipeline SQL or infer behavior from Parquet.
3. Build `source_query` from the mapping: select the mapped dimensions and measures, join only the mapped source tables and keys, apply only mapped transformations and filters, alias every output column, and group by the mapped grain.
4. Create module-scoped `source_data` and `target_data` fixtures using PostgreSQL for expected data and `ParquetReader` for actual data, including partition subfolders.
5. Add the five tests from the template. Pass the explicitly identified partition columns to completeness, the mapped grain to `check_duplicates`, and all mapped output columns to `check_not_null_values`.
6. If partition columns are present, validate their documented relationship to business columns with the reusable DQ library.
7. Review the generated module against the hard rules and self-review checklist. Do not generate modules for other datasets unless requested separately.

## Template

Use this full module shape, replacing every placeholder with the requested mapping and supplied metadata. Do not leave placeholder column names, markers, dataset names, or SQL in a completed module.

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): <requirement_id>
Author(s): <author_name>
"""

import pytest


@pytest.fixture(scope='module')
def source_data(db_connection):
    source_query = """
    <mapping-derived SQL selecting and aliasing the mapped output columns>
    """
    return db_connection.get_data_sql(source_query)


@pytest.fixture(scope='module')
def target_data(parquet_reader):
    target_path = '/parquet_data/<dataset_name>'
    return parquet_reader.process(target_path, include_subfolders=True)


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.<dataset_name>
def test_check_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_data_completeness(source_data, target_data, data_quality_library):
    data_quality_library.check_data_completeness(
        source_data,
        target_data,
        allowed_partition_columns=['<technical_partition_column>'],
    )


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_count(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_uniqueness(target_data, data_quality_library):
    data_quality_library.check_duplicates(
        target_data, column_names=['<grain_column_1>', '<grain_column_2>']
    )


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(
        target_data, ['<mapped_output_column_1>', '<mapped_output_column_2>']
    )
```

Supply every mapped grain column in the uniqueness list and every mapped output column in the not-null list; the sample list lengths above are illustrative only.

## SQL derivation (generic)

Derive the expected query from business mapping, not from implementation:

1. Identify the mapped source tables, join path, and join keys.
2. Select all mapped dimensions and measures. Group by exactly the mapped grain.
3. Apply the aggregation, concatenation/formatting, rounding, and date-grain behavior only as specified by the mapping.
4. Alias each selected expression to its exact target column name.
5. Add a filter only when the mapping explicitly defines one. A mapping note or sample value is not permission to invent a filter.
6. If any required behavior is unclear or contradictory, stop and ask. Do not resolve ambiguity by reading `data_dev/`, matching the current Parquet output, or weakening the expected query.

## After generation

Check that the file is in the required location, contains all five tests and correct markers, compares PostgreSQL expected data to Parquet actual data, and uses the mapped grain and output columns. Run pytest only if the user asks or the task explicitly includes execution. Report any observed mismatch as a data defect to investigate; never rewrite mapping-derived SQL to force a green result.

---

## Skill review (self-check before Step 3)

Confirm every item below is true before proceeding to Step 3:

- [x] This skill contains no concrete expected SQL for `facility_name_min_time_spent_per_visit_date`, `facility_type_avg_time_spent_per_visit_date`, or `patient_sum_treatment_cost_per_facility_type`.
- [x] This skill never directs the agent to use `data_dev/` or parquet-loader SQL.
- [x] It defines completeness, count, uniqueness on mapped grain, and not-null checks, as well as the smoke check.
- [x] It allows only explicitly identified technical partition columns in completeness comparisons; unlisted extras and missing mapped columns remain failures.
- [x] It keeps PostgreSQL as source and Parquet as target, and prohibits trivial always-pass checks.
- [x] All required sections are complete and contain no unresolved placeholders.
