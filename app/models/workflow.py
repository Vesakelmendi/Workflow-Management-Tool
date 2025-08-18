from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..utils.enums import NodeStatus


class Node(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    dependencies: List[int] = []  # List of node IDs that must be completed first
    assigned_user_id: Optional[int] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    metadata: Dict[str, Any] = {}


class Workflow(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    nodes: List[Node] = []
    owner_id: int
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    is_active: bool = True


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int


class NodeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dependencies: List[int] = []
    assigned_user_id: Optional[int] = None
    metadata: Dict[str, Any] = {}
