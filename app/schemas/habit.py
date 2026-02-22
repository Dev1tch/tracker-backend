from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum

class HabitPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    NORMAL = "Normal"

# --- Category Schemas ---
class HabitCategoryBase(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None

class HabitCategoryCreate(HabitCategoryBase):
    pass

class HabitCategory(HabitCategoryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Habit Schemas ---
class HabitBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    priority: HabitPriority = HabitPriority.NORMAL
    is_active: bool = True

class HabitCreate(HabitBase):
    pass

class HabitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    priority: Optional[HabitPriority] = None
    is_active: Optional[bool] = None

class Habit(HabitBase):
    id: UUID
    created_at: datetime
    # We can include category details here if needed later via a flat or nested model

    class Config:
        from_attributes = True

# --- Habit Log Schemas ---
class HabitLogBase(BaseModel):
    habit_id: UUID
    date: date
    is_successful: bool
    comment: Optional[str] = None

class HabitLogCreate(HabitLogBase):
    pass

class HabitLog(HabitLogBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class HabitLogUpdate(BaseModel):
    is_successful: Optional[bool] = None
    comment: Optional[str] = None
    date: Optional[date] = None
