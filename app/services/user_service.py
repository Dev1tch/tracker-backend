from app.core.supabase_client import SupabaseClient
from app.core.security import fake_verify_password, get_password_hash, verify_password
from app.schemas.user import UserCreate
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

    def authenticate(self, email: str, password: str):
        """Authenticate a user by email and password.

        Takes plain strings (not an EmailStr-validated model) so a malformed
        login identifier can't raise a ValidationError -> 500; it simply matches
        no user. Runs a constant-time dummy bcrypt check on the no-user path so
        timing doesn't reveal whether the email is registered.
        """
        user = self.get_by_email(email)
        if not user:
            fake_verify_password(password)
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return user

    def get_by_id(self, user_id: UUID):
        """Get a user by ID."""
        response = self.db.read(self.table_name, filters={"id": str(user_id)})
        return response.data[0] if response.data else None
