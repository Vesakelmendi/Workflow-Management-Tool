from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..utils.enums import NodeStatus

class Node(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    dependencies: List[int] = []
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
    read_roles: List[str] = []   
    write_roles: List[str] = []  

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int
    read_roles: Optional[List[str]] = None
    write_roles: Optional[List[str]] = None

class NodeCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    dependencies: List[int] = []
    assigned_user_id: Optional[int] = None
    metadata: Dict[str, Any] = {}
