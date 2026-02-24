from uuid import UUID
from app.core.supabase_client import SupabaseClient
from app.schemas.habit import HabitCategoryCreate, HabitCategoryUpdate

class CategoryService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "habit_categories"

    def create(self, user_id: UUID, category_data: HabitCategoryCreate):
        data = category_data.model_dump(mode='json')
        data["user_id"] = str(user_id)
        response = self.db.create(self.table_name, data)
        return response.data[0] if response.data else None

    def get_all(self, user_id: UUID):
        response = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return response.data

    def get_by_id(self, user_id: UUID, category_id: UUID):
        response = self.db.read(
            self.table_name, 
            filters={"id": str(category_id), "user_id": str(user_id)}
        )
        return response.data[0] if response.data else None

    def delete(self, user_id: UUID, category_id: UUID):
        response = self.db.delete(
            self.table_name, 
            filters={"id": str(category_id), "user_id": str(user_id)}
        )
        return len(response.data) > 0 if response.data else False

    def update(self, user_id: UUID, category_id: UUID, category_data: HabitCategoryUpdate):
        data = category_data.model_dump(exclude_unset=True)
        if not data:
            return self.get_by_id(user_id, category_id)
            
        response = self.db.update(
            self.table_name,
            filters={"id": str(category_id), "user_id": str(user_id)},
            data=data
        )
        return response.data[0] if response.data else None
