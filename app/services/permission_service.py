from ..models.workflow import Workflow
from .auth_service import AuthService

class PermissionService:

    @staticmethod
    def check_read_permission(user_id: int, workflow_id: int) -> bool:
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        user = AuthService.get_user_by_id(user_id)

        if not workflow or not user:
            return False

        # Admins always allowed
        if any(r.name == "Admin" for r in user.roles):
            return True

        # Owner always allowed
        if workflow.owner_id == user_id:
            return True

        # Role-based read (read_roles OR write_roles)
        user_roles = [r.name for r in user.roles]
        if any(role in workflow.read_roles for role in user_roles) or \
           any(role in workflow.write_roles for role in user_roles):
            return True

        return False

    @staticmethod
    def check_write_permission(user_id: int, workflow_id: int) -> bool:
        from .workflow_service import WorkflowService
        workflow = WorkflowService.get_workflow_by_id(workflow_id)
        user = AuthService.get_user_by_id(user_id)

        if not workflow or not user:
            return False

        # Admins always allowed
        if any(r.name == "Admin" for r in user.roles):
            return True

        # Owner always allowed
        if workflow.owner_id == user_id:
            return True

        # Role-based write
        user_roles = [r.name for r in user.roles]
        return any(role in workflow.write_roles for role in user_roles)

    @staticmethod
    def check_execute_permission(user_id: int, workflow_id: int) -> bool:
        # Execution is treated same as write
        return PermissionService.check_write_permission(user_id, workflow_id)
