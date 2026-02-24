from app.core.supabase_client import SupabaseClient
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserLogin
from uuid import UUID

class UserService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "users"

    def create(self, user_in: UserCreate):
        """Create a new user with hashed password."""
        user_data = user_in.model_dump()
        password = user_data.pop("password")
        user_data["password_hash"] = get_password_hash(password)
        
        response = self.db.create(self.table_name, user_data)
        return response.data[0] if response.data else None

    def get_by_email(self, email: str):
        """Get a user by email."""
        response = self.db.read(self.table_name, filters={"email": email.lower()})
        return response.data[0] if response.data else None

    def authenticate(self, login_data: UserLogin):
        """Authenticate a user by email and password."""
        user = self.get_by_email(login_data.email)
        if not user:
            return None
        if not verify_password(login_data.password, user["password_hash"]):
            return None
        return user

    def get_by_id(self, user_id: UUID):
        """Get a user by ID."""
        response = self.db.read(self.table_name, filters={"id": str(user_id)})
        return response.data[0] if response.data else None
