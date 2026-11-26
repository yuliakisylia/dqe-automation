from pathlib import Path

import pandas as pd


class ParquetReader:
    def process(self, path: str, include_subfolders: bool = False) -> pd.DataFrame:
        parquet_path = Path(path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet path does not exist: {path}")

        if parquet_path.is_file():
            if parquet_path.suffix.lower() != ".parquet":
                raise ValueError(f"Expected a Parquet file, got: {path}")
            return pd.read_parquet(parquet_path, engine="pyarrow")

        if not parquet_path.is_dir():
            raise ValueError(f"Parquet path is not a file or directory: {path}")

        parquet_files = (
            list(parquet_path.rglob("*.parquet"))
            if include_subfolders
            else list(parquet_path.glob("*.parquet"))
        )
        if not parquet_files:
            scope = "or its subfolders" if include_subfolders else "at its top level"
            raise FileNotFoundError(f"No Parquet files found {scope}: {path}")

        if include_subfolders:
            return pd.read_parquet(parquet_path, engine="pyarrow")

        dataframes = [
            pd.read_parquet(file_path, engine="pyarrow")
            for file_path in sorted(parquet_files)
        ]
        return pd.concat(dataframes, ignore_index=True)
