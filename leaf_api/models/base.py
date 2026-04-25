from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """Base model with common fields - abstract base for all models"""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
