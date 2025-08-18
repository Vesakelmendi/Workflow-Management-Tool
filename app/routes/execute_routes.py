from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..services.workflow_service import WorkflowService
from ..services.permission_service import PermissionService
from ..utils.enums import NodeStatus


router = APIRouter(prefix="/api", tags=["execution"])


class ExecutionRequest(BaseModel):
    user_id: int
    parameters: Optional[Dict[str, Any]] = {}


class ExecutionResponse(BaseModel):
    success: bool
    message: str
    execution_result: Dict[str, Any]


class NodeStatusUpdate(BaseModel):
    status: NodeStatus
    user_id: int


@router.post("/workflows/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(
    workflow_id: int,
    execution_data: ExecutionRequest
):
    """Execute a workflow"""
    try:
        # Check execute permission
        if not PermissionService.check_execute_permission(execution_data.user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to execute this workflow"
            )
        
        # Verify workflow exists
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        if not workflow.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot execute inactive workflow"
            )
        
        # Execute the workflow
        execution_result = WorkflowService.execute_workflow(workflow_id, execution_data.user_id)
        
        if execution_result["success"]:
            return ExecutionResponse(
                success=True,
                message="Workflow executed successfully",
                execution_result=execution_result
            )
        else:
            return ExecutionResponse(
                success=False,
                message="Workflow execution completed with errors",
                execution_result=execution_result
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.put("/workflows/{workflow_id}/nodes/{node_id}/status")
async def update_node_status(
    workflow_id: int,
    node_id: int,
    status_update: NodeStatusUpdate
):
    """Update the status of a specific node in a workflow"""
    try:
        # Check write permission for the workflow
        if not PermissionService.check_write_permission(status_update.user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this workflow"
            )
        
        # Verify workflow and node exist
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        node = WorkflowService.get_node_by_id(workflow_id, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        # Update node status
        success = WorkflowService.update_node_status(workflow_id, node_id, status_update.status)
        
        if success:
            return {
                "success": True,
                "message": f"Node {node_id} status updated to {status_update.status.value}",
                "workflow_id": workflow_id,
                "node_id": node_id,
                "new_status": status_update.status.value
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update node status"
            )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update node status: {str(e)}"
        )


@router.get("/workflows/{workflow_id}/nodes/{node_id}/status")
async def get_node_status(
    workflow_id: int,
    node_id: int,
    user_id: int = Query(..., description="User ID for permission checking")
):
    """Get the current status of a specific node"""
    try:
        # Check read permission
        if not PermissionService.check_read_permission(user_id, workflow_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this workflow"
            )
        
        # Get the node
        node = WorkflowService.get_node_by_id(workflow_id, node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Node not found"
            )
        
        return {
            "workflow_id": workflow_id,
            "node_id": node_id,
            "status": node.status.value,
            "updated_at": node.updated_at,
            "assigned_user_id": node.assigned_user_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get node status: {str(e)}"
        )
