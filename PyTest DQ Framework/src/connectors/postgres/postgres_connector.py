import pandas as pd
import psycopg2


class PostgresConnectorContextManager:
    def __init__(
        self,
        db_host: str,
        db_name: str,
        db_port: int,
        db_user: str,
        db_password: str,
    ):
        self.db_host = db_host
        self.db_name = db_name
        self.db_port = db_port
        self.db_user = db_user
        self.db_password = db_password
        self.connection = None

    def __enter__(self):
        self.connection = psycopg2.connect(
            host=self.db_host,
            dbname=self.db_name,
            port=self.db_port,
            user=self.db_user,
            password=self.db_password,
        )
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        return False

    def get_data_sql(self, sql: str) -> pd.DataFrame:
        if self.connection is None or self.connection.closed:
            raise RuntimeError("The PostgreSQL connection is not open.")
        return pd.read_sql_query(sql, self.connection)
