from pydantic import BaseModel
from typing import List, Optional


class Role(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: List[str] = []  # e.g., ["read", "write", "execute"]
