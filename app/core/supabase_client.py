import time
from typing import Any, Callable, Dict, List, Optional, Union

import httpx
from supabase import create_client, Client
from app.core.config import settings


TRANSIENT_SUPABASE_ERRORS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.WriteError,
    httpx.WriteTimeout,
)


class SupabaseClient:
    def __init__(self, client: Optional[Client] = None):
        self.client: Client = client or create_client(
            settings.SUPABASE_URL, settings.SUPABASE_KEY
        )

    def _execute_with_retry(self, execute: Callable[[], Any]) -> Any:
        last_error = None
        for attempt in range(3):
            try:
                return execute()
            except TRANSIENT_SUPABASE_ERRORS as error:
                last_error = error
                if attempt == 2:
                    break
                time.sleep(0.15 * (attempt + 1))
        raise last_error

    def table(self, table_name: str):
        """Returns a query builder for the specified table."""
        return self.client.table(table_name)

    def create(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Any:
        """Create one or more rows in a table."""
        return self._execute_with_retry(
            lambda: self.client.table(table_name).insert(data).execute()
        )

    def read(
        self, 
        table_name: str, 
        select: str = "*", 
        filters: Optional[Dict[str, Any]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Any:
        """Read rows from a table with optional filters, ordering, and limits."""
        query = self.client.table(table_name).select(select)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if order:
            # Assumes order is simplified e.g. "created_at.desc"
            col, direction = order.split('.')
            query = query.order(col, desc=(direction == 'desc'))
            
        if limit:
            query = query.limit(limit)
            
        return self._execute_with_retry(lambda: query.execute())

    def update(self, table_name: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Any:
        """Update rows in a table matching the filters."""
        query = self.client.table(table_name).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        return self._execute_with_retry(lambda: query.execute())

    def delete(self, table_name: str, filters: Dict[str, Any]) -> Any:
        """Delete rows in a table matching the filters."""
        query = self.client.table(table_name).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return self._execute_with_retry(lambda: query.execute())

    def rpc(self, fn_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Call a Postgres function/RPC."""
        return self._execute_with_retry(
            lambda: self.client.rpc(fn_name, params or {}).execute()
        )
