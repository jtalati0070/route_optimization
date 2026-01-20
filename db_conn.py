import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from typing import Any, List, Tuple, Optional


class PostgresConnectionPool:
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        minconn: int = 1,
        maxconn: int = 10,
    ):
        self._pool = pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

    @contextmanager
    def get_conn(self):
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def close_all(self):
        self._pool.closeall()


class PostgresClient:
    def __init__(self, connection_pool: PostgresConnectionPool):
        self.pool = connection_pool

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch: bool = True,
    ) -> Optional[List[Tuple]]:
        """
        Execute any SQL query safely.

        Args:
            query: SQL query with placeholders (%s)
            params: tuple of parameters
            fetch: if True, returns fetched rows

        Returns:
            List of rows or None
        """
        with self.pool.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)

                if fetch:
                    result = cur.fetchall()
                else:
                    result = None

                conn.commit()
                return result
