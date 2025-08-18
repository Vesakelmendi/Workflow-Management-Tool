from typing import List
from ..models.workflow import Workflow
from ..models.user import User
from .auth_service import AuthService


# In-memory storage for workflow permissions
workflow_permissions_db = {}  # workflow_id -> {user_id: [permissions]}


class PermissionService:
    @staticmethod
    def check_read_permission(user_id: int, workflow_id: int) -> bool:
        """Check if user has read permission for a workflow"""
        # Workflow owner always has full access
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if workflow and workflow.owner_id == user_id:
            return True
        
        # Check admin permissions
        if AuthService.validate_user_role(user_id, "admin"):
            return True
        
        # Check explicit workflow permissions
        workflow_perms = workflow_permissions_db.get(workflow_id, {})
        user_perms = workflow_perms.get(user_id, [])
        
        return "read" in user_perms or "write" in user_perms

    @staticmethod
    def check_write_permission(user_id: int, workflow_id: int) -> bool:
        """Check if user has write permission for a workflow"""
        # Workflow owner always has full access
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if workflow and workflow.owner_id == user_id:
            return True
        
        # Check admin permissions
        if AuthService.validate_user_role(user_id, "admin"):
            return True
        
        # Check explicit workflow permissions
        workflow_perms = workflow_permissions_db.get(workflow_id, {})
        user_perms = workflow_perms.get(user_id, [])
        
        return "write" in user_perms

    @staticmethod
    def check_execute_permission(user_id: int, workflow_id: int) -> bool:
        """Check if user has execute permission for a workflow"""
        # Workflow owner always has full access
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if workflow and workflow.owner_id == user_id:
            return True
        
        # Check admin permissions
        if AuthService.validate_user_role(user_id, "admin"):
            return True
        
        # Check if user has execute permission in their role
        if AuthService.validate_user_role(user_id, "execute"):
            # Check if they have at least read access to this workflow
            return PermissionService.check_read_permission(user_id, workflow_id)
        
        # Check explicit workflow permissions
        workflow_perms = workflow_permissions_db.get(workflow_id, {})
        user_perms = workflow_perms.get(user_id, [])
        
        return "execute" in user_perms

    @staticmethod
    def grant_workflow_permission(workflow_id: int, user_id: int, permission: str) -> bool:
        """Grant a specific permission to a user for a workflow"""
        if permission not in ["read", "write", "execute"]:
            return False
        
        if workflow_id not in workflow_permissions_db:
            workflow_permissions_db[workflow_id] = {}
        
        if user_id not in workflow_permissions_db[workflow_id]:
            workflow_permissions_db[workflow_id][user_id] = []
        
        if permission not in workflow_permissions_db[workflow_id][user_id]:
            workflow_permissions_db[workflow_id][user_id].append(permission)
        
        return True

    @staticmethod
    def revoke_workflow_permission(workflow_id: int, user_id: int, permission: str) -> bool:
        """Revoke a specific permission from a user for a workflow"""
        workflow_perms = workflow_permissions_db.get(workflow_id, {})
        user_perms = workflow_perms.get(user_id, [])
        
        if permission in user_perms:
            user_perms.remove(permission)
            return True
        
        return False

    @staticmethod
    def get_user_workflow_permissions(user_id: int, workflow_id: int) -> List[str]:
        """Get all permissions a user has for a specific workflow"""
        permissions = []
        
        # Check if user is owner
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        if workflow and workflow.owner_id == user_id:
            return ["read", "write", "execute"]
        
        # Check admin permissions
        if AuthService.validate_user_role(user_id, "admin"):
            return ["read", "write", "execute"]
        
        # Check explicit workflow permissions
        workflow_perms = workflow_permissions_db.get(workflow_id, {})
        user_perms = workflow_perms.get(user_id, [])
        
        # Add role-based permissions
        user_role_perms = AuthService.get_user_permissions(user_id)
        if "execute" in user_role_perms and ("read" in user_perms or "write" in user_perms):
            user_perms.append("execute")
        
        return list(set(user_perms))

    @staticmethod
    def get_workflow_users_with_permissions(workflow_id: int) -> dict:
        """Get all users who have explicit permissions for a workflow"""
        return workflow_permissions_db.get(workflow_id, {})
