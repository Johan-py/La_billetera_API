from httpx import Client, Timeout
from typing import Any
from app.config import settings

from fastapi.encoders import jsonable_encoder

class SupabaseClient:
    def __init__(self):
        self.url = settings.supabase_url.rstrip("/")
        self.key = settings.supabase_key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self.client = Client(base_url=self.url, headers=self.headers, timeout=Timeout(30.0))

    def table(self, table_name: str) -> "TableBuilder":
        return TableBuilder(self, table_name)


class TableBuilder:
    def __init__(self, db: "SupabaseClient", table_name: str):
        self.db = db
        self.table_name = table_name
        self._filters: list[tuple[str, str, Any]] = []
        self._order_col: str | None = None
        self._order_dir: bool = True
        self._range_start: int | None = None
        self._range_end: int | None = None
        self._limit_val: int | None = None
        self._select_columns: str = "*"
        self._count: str | None = None

    def select(self, columns: str = "*", count: str | None = None):
        self._select_columns = columns
        self._count = count
        return self

    def eq(self, column: str, value: Any):
        self._filters.append(("eq", column, value))
        return self

    def gte(self, column: str, value: Any):
        self._filters.append(("gte", column, value))
        return self

    def lte(self, column: str, value: Any):
        self._filters.append(("lte", column, value))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_dir = desc
        return self

    def range(self, start: int, end: int):
        self._range_start = start
        self._range_end = end
        return self

    def limit(self, val: int):
        self._limit_val = val
        return self

    def _build_query_params(self) -> dict:
        params = {}
        if self._select_columns:
            params["select"] = self._select_columns
        if self._count:
            params["count"] = self._count
        return params

    def _build_filter_query(self) -> str:
        query = f"/rest/v1/{self.table_name}"
        filters = []
        for op, col, val in self._filters:
            if op == "eq":
                filters.append(f"{col}=eq.{val}")
            elif op == "gte":
                filters.append(f"{col}=gte.{val}")
            elif op == "lte":
                filters.append(f"{col}=lte.{val}")
        if filters:
            query += "?" + "&".join(filters)
        return query

    def _add_order_and_range(self, url: str) -> str:
        parts = [url]
        if self._order_col:
            direction = "desc" if self._order_dir else "asc"
            parts.append(f"order={self._order_col}.{direction}")
        if self._range_start is not None and self._range_end is not None:
            parts.append(f"offset={self._range_start}")
            parts.append(f"limit={self._range_end - self._range_start + 1}")
        if self._limit_val:
            parts.append(f"limit={self._limit_val}")
        if len(parts) > 1:
            separator = "&" if "?" in url else "?"
            return url + separator + "&".join(parts[1:])
        return url

    def execute(self):
        url = self._build_filter_query()
        url = self._add_order_and_range(url)
        headers = self.db.headers.copy()

        if self._select_columns:
            headers["Accept"] = "application/json"

        response = self.db.client.get(url, headers=headers)
        response.raise_for_status()
        return QueryResult(response.json(), response.headers)


    def insert(self, data: dict | list):
        url = f"/rest/v1/{self.table_name}"
        headers = self.db.headers.copy()
        response = self.db.client.post(
            url,
            json=jsonable_encoder(data),
            headers=headers
)
        response.raise_for_status()
        return QueryResult(response.json(), response.headers)

    def update(self, data: dict):
        url = self._build_filter_query()
        headers = self.db.headers.copy()
        response = self.db.client.patch(
            url,
            json=jsonable_encoder(data),
            headers=headers
)
        response.raise_for_status()
        return QueryResult(response.json(), response.headers)

    def delete(self):
        url = self._build_filter_query()
        headers = self.db.headers.copy()
        response = self.db.client.delete(url, headers=headers)
        response.raise_for_status()
        return QueryResult(response.json(), response.headers)


class QueryResult:
    def __init__(self, data: list, headers=None):
        self.data = data
        self.headers = headers or {}

    @property
    def count(self) -> int | None:
        count_str = self.headers.get("content-range", "")
        if count_str and "/" in count_str:
            try:
                return int(count_str.split("/")[1])
            except (ValueError, IndexError):
                pass
        return len(self.data)


supabase = SupabaseClient()


def get_db() -> SupabaseClient:
    return supabase
