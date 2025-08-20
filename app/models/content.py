from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from ..utils.enums import ContentType, Priority


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    workflow_id: int
    node_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    created_by: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    due_date: Optional[datetime] = None
    is_completed: bool = False


class Note(BaseModel):
    id: int
    title: str
    content: str
    workflow_id: int
    node_id: Optional[int] = None
    created_by: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    tags: list[str] = []


class Attachment(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    workflow_id: int
    node_id: Optional[int] = None
    uploaded_by: int
    uploaded_at: datetime = datetime.now()
    description: Optional[str] = None


class Content(BaseModel):
    id: int
    content_type: ContentType
    workflow_id: int
    node_id: Optional[int] = None
    data: Dict[str, Any]  # Stores the actual task/note/attachment data
    created_by: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()



