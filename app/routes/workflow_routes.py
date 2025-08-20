from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from ..services.workflow_service import WorkflowService
from ..services.permission_service import PermissionService
from ..services.auth_service import AuthService
from ..models.workflow import Workflow, WorkflowCreate, NodeCreate
from ..models.content import Content, ContentType

router = APIRouter(prefix="/api", tags=["workflows"])

# Workflow Endpoints
@router.get("/workflows", response_model=List[Workflow])
async def get_workflows(
    user_id: int = Query(..., description="User ID for permission checking"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID")
):
    try:
        workflows = (
            [wf for wf in WorkflowService.get_all_workflows() if wf.owner_id == owner_id]
            if owner_id else WorkflowService.get_all_workflows()
        )
        return [wf for wf in workflows if PermissionService.check_read_permission(user_id, wf.id)]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflows: {str(e)}"
        )

@router.post("/workflows", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    user_id: int = Query(..., description="User ID for permission checking")
):
    if not AuthService.validate_user_role(user_id, "write"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to create workflows")

    workflow_data.owner_id = user_id
    return WorkflowService.create_workflow(workflow_data, workflow_data.read_roles, workflow_data.write_roles)

@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if not PermissionService.check_read_permission(user_id, workflow_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this workflow")

    return workflow

@router.put("/workflows/{workflow_id}/roles")
async def update_workflow_roles(
    workflow_id: int,
    read_roles: List[str] = Query([]),
    write_roles: List[str] = Query([]),
    user_id: int = Query(..., description="User ID for permission checking")
):
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only owner can update roles")

    workflow.read_roles = read_roles
    workflow.write_roles = write_roles
    return {"success": True, "read_roles": workflow.read_roles, "write_roles": workflow.write_roles}    

@router.get("/workflows/{workflow_id}/statistics")
async def get_workflow_statistics(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if not PermissionService.check_read_permission(user_id, workflow_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to view workflow statistics")

    return WorkflowService.get_workflow_statistics(workflow_id)

# Workflow Content Endpoints
@router.get("/workflows/{workflow_id}/content", response_model=List[Content])
async def get_workflow_content(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if not PermissionService.check_read_permission(user_id, workflow_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to access this workflow content")

    return WorkflowService.get_workflow_content(workflow_id, user_id)

@router.post("/workflows/{workflow_id}/content", response_model=Content, status_code=status.HTTP_201_CREATED)
async def add_content_to_workflow(
    workflow_id: int,
    content_type: ContentType,
    data: dict,
    user_id: int = Query(..., description="User ID creating the content"),
    node_id: Optional[int] = None
):
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if not PermissionService.check_write_permission(user_id, workflow_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to add content to this workflow")

    try:
        content = WorkflowService.add_content(workflow_id, content_type, data, user_id, node_id)
        return content
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Node Management Endpoints
@router.post("/workflows/{workflow_id}/nodes", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_node_to_workflow(
    workflow_id: int,
    node_data: NodeCreate,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Add a new node to a workflow"""
    workflow = WorkflowService.get_workflow_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    if not PermissionService.check_write_permission(user_id, workflow_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission to modify this workflow")

    try:
        node = WorkflowService.add_node_to_workflow(workflow_id, node_data)
        if node:
            return {"success": True, "node": node, "message": f"Node '{node.name}' added to workflow"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add node")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to add node: {str(e)}")
