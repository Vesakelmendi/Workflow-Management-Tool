from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from ..services.workflow_service import WorkflowService
from ..services.permission_service import PermissionService
from ..models.workflow import Workflow, WorkflowCreate
from ..models.content import Content


router = APIRouter(prefix="/api", tags=["workflows"])


@router.get("/workflows", response_model=List[Workflow])
async def get_workflows(
    user_id: int = Query(..., description="User ID for permission checking"),
    owner_id: Optional[int] = Query(None, description="Filter by owner ID")
):
    """Get all workflows that the user has access to"""
    try:
        if owner_id:
            # Get workflows by specific owner
            workflows = WorkflowService.get_workflows_by_user(owner_id)
        else:
            # Get all workflows
            workflows = WorkflowService.get_all_workflows()
        
        # Filter workflows based on user permissions
        accessible_workflows = []
        for workflow in workflows:
            if PermissionService.check_read_permission(user_id, workflow.id):
                accessible_workflows.append(workflow)
        
        return accessible_workflows
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Get a specific workflow by ID"""
    try:
        # Check read permission
        if not PermissionService.check_read_permission(user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return workflow
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/content", response_model=List[Content])
async def get_workflow_content(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Get all content associated with a workflow"""
    try:
        # Check read permission
        if not PermissionService.check_read_permission(user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow content"
            )
        
        # Verify workflow exists
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        content = WorkflowService.get_workflow_content(workflow_id)
        return content
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow content: {str(e)}"
        )


@router.post("/workflows", response_model=Workflow)
async def create_workflow(
    workflow_data: WorkflowCreate,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Create a new workflow"""
    try:
        # Verify the user can create workflows (has write permission in general)
        from ..services.auth_service import AuthService
        if not AuthService.validate_user_role(user_id, "write"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create workflows"
            )
        
        # Set the owner to the requesting user
        workflow_data.owner_id = user_id
        
        workflow = WorkflowService.create_workflow(workflow_data)
        return workflow
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/statistics")
async def get_workflow_statistics(
    workflow_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Get statistics for a workflow"""
    try:
        # Check read permission
        if not PermissionService.check_read_permission(user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        stats = WorkflowService.get_workflow_statistics(workflow_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve workflow statistics: {str(e)}"
        )
