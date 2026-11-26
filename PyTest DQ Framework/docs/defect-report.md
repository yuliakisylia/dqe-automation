# PyTest DQ Framework — Defect Report

## Jenkins build #8

The run executed **15 tests: 7 passed and 8 failed**. The failures are consistent with transformation defects described below. The HTML test report is archived with Jenkins build #8.

## Data defects

### 1. Duplicate clinic aggregates

- **Affected dataset:** `facility_name_min_time_spent_per_visit_date`
- **Expected result:** 35,493 rows, with one result per `facility_name` and `visit_date`.
- **Actual result:** 44,328 rows. There are 8,835 duplicated grain combinations, involving 17,670 rows.
- **Root cause:** The transformation first aggregates all facilities, then uses `UNION ALL` to add clinic aggregates again. This adds a second copy of each clinic group.
- **Supporting evidence:** The mapping defines the facility/date grain with no filter ([mapping](../../docs/parquet-aggregated-data-mapping.md#facility_name_min_time_spent_per_visit_date)). The duplicate clinic branch is in the transformation query ([query](../../data_dev/queries.py#L184), [clinic filter](../../data_dev/queries.py#L205)).

### 2. Missing facility-type/date aggregates

- **Affected dataset:** `facility_type_avg_time_spent_per_visit_date`
- **Expected result:** 35,493 rows covering the mapped facility types and visit dates, with no filters.
- **Actual result:** 25,803 rows, or 9,690 fewer than expected. The Parquet data contains Hospital, Clinic, and Specialty Center rows, but no Urgent Care rows; its earliest date is 2000-11-01.
- **Root cause:** The transformation filters out earlier timestamps and limits the facility types to three, excluding Urgent Care. The mapping specifies no filters.
- **Supporting evidence:** The mapping’s no-filter rule and date partition are documented [here](../../docs/parquet-aggregated-data-mapping.md#facility_type_avg_time_spent_per_visit_date); the transformation filters are [here](../../data_dev/queries.py#L150). The timestamp comparison is against midnight at the start of 2000-11-01, so later visits on that date may still appear.

### 3. Null patient names collapse groups

- **Affected dataset:** `patient_sum_treatment_cost_per_facility_type`
- **Expected result:** 120 rows grouped by `facility_type` and full patient name; `full_name` is not null.
- **Actual result:** 64 rows, including four null `full_name` values—one per facility type.
- **Root cause:** The transformation assigns `NULL` to names for patient IDs 1–15. Those patients are then combined into one null-name group per facility type, reducing the group count.
- **Supporting evidence:** The mapping requires a non-null full name and groups by it ([mapping](../../docs/parquet-aggregated-data-mapping.md#patient_sum_treatment_cost_per_facility_type)). The null-producing `CASE` expression is in the [transformation query](../../data_dev/queries.py#L161).

### 4. Clinic treatment costs are negative

- **Affected dataset:** `patient_sum_treatment_cost_per_facility_type`
- **Expected result:** The mapped `SUM(treatment_cost)`, which the mapping specifies cannot be negative.
- **Actual result:** Parquet inspection found 16 negative Clinic aggregates; the minimum was -26,483,486.57.
- **Root cause:** The transformation negates `SUM(treatment_cost)` for Clinic rows instead of using the mapped sum.
- **Supporting evidence:** The non-negative requirement is in the [mapping](../../docs/parquet-aggregated-data-mapping.md#patient_sum_treatment_cost_per_facility_type); the sign change is in the [transformation query](../../data_dev/queries.py#L167). This is not a separate test assertion; it contributes to the source-to-target completeness failure.

## Resolved framework issue — not a data defect

The `partition_date` and `facility_type_partition` values are partition metadata reconstructed by PyArrow when the dataset is read, not physical business columns in the Parquet files. The framework now allows only the explicitly named partition columns during completeness comparison and separately checks that their values match the mapped business fields. This resolved schema mismatch is distinct from the transformation defects above.
