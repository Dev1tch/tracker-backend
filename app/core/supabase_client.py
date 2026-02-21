from typing import Any, Dict, List, Optional, Union
from supabase import create_client, Client
from app.core.config import settings

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def table(self, table_name: str):
        """Returns a query builder for the specified table."""
        return self.client.table(table_name)

    def create(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Any:
        """Create one or more rows in a table."""
        return self.client.table(table_name).insert(data).execute()

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
            
        return query.execute()

    def update(self, table_name: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Any:
        """Update rows in a table matching the filters."""
        query = self.client.table(table_name).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute()

    def delete(self, table_name: str, filters: Dict[str, Any]) -> Any:
        """Delete rows in a table matching the filters."""
        query = self.client.table(table_name).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute()

    def rpc(self, fn_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Call a Postgres function/RPC."""
        return self.client.rpc(fn_name, params or {}).execute()

# Global instance
supabase = SupabaseClient()
