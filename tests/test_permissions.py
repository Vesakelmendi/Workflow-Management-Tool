import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.permission_service import PermissionService, workflow_permissions_db
from app.services.workflow_service import WorkflowService, workflows_db
from app.services.auth_service import AuthService, users_db, roles_db
from app.models.workflow import WorkflowCreate
from app.models.user import UserCreate, User

client = TestClient(app)


class TestPermissions:
    def setup_method(self):
        """Reset test data before each test"""
        workflows_db.clear()
        workflow_permissions_db.clear()
        
        # Reset users to just admin
        users_db.clear()
        admin_role = next((r for r in roles_db if r.name == "admin"), None)
        user_role = next((r for r in roles_db if r.name == "user"), None)
        
        if admin_role:
            admin_user = User(
                id=1,
                email="admin@example.com",
                username="admin",
                password="admin123",
                roles=[admin_role]
            )
            users_db.append(admin_user)
        
        if user_role:
            regular_user = User(
                id=2,
                email="user@example.com",
                username="user",
                password="user123",
                roles=[user_role]
            )
            users_db.append(regular_user)

    def test_workflow_owner_permissions(self):
        """Test that workflow owners have full access"""
        # Create workflow owned by user 2
        workflow_data = WorkflowCreate(name="Owner Test Workflow", owner_id=2)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Owner should have all permissions
        assert PermissionService.check_read_permission(2, workflow.id) is True
        assert PermissionService.check_write_permission(2, workflow.id) is True
        assert PermissionService.check_execute_permission(2, workflow.id) is True

    def test_admin_permissions(self):
        """Test that admins have access to all workflows"""
        # Create workflow owned by user 2
        workflow_data = WorkflowCreate(name="Admin Test Workflow", owner_id=2)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Admin (user 1) should have all permissions even though not owner
        assert PermissionService.check_read_permission(1, workflow.id) is True
        assert PermissionService.check_write_permission(1, workflow.id) is True
        assert PermissionService.check_execute_permission(1, workflow.id) is True

    def test_no_permission_by_default(self):
        """Test that users have no permissions by default"""
        # Create workflow owned by user 1
        workflow_data = WorkflowCreate(name="No Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Create a third user with no special roles
        viewer_role = next((r for r in roles_db if r.name == "viewer"), None)
        test_user = User(
            id=3,
            email="test@example.com",
            username="testuser",
            password="test123",
            roles=[viewer_role] if viewer_role else []
        )
        users_db.append(test_user)
        
        # User 3 should have no permissions
        assert PermissionService.check_read_permission(3, workflow.id) is False
        assert PermissionService.check_write_permission(3, workflow.id) is False
        assert PermissionService.check_execute_permission(3, workflow.id) is False

    def test_grant_and_revoke_permissions(self):
        """Test granting and revoking workflow permissions"""
        workflow_data = WorkflowCreate(name="Permission Grant Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Grant read permission to user 2
        success = PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        assert success is True
        
        # User 2 should now have read permission
        assert PermissionService.check_read_permission(2, workflow.id) is True
        assert PermissionService.check_write_permission(2, workflow.id) is False
        
        # Grant write permission
        PermissionService.grant_workflow_permission(workflow.id, 2, "write")
        assert PermissionService.check_write_permission(2, workflow.id) is True
        
        # Revoke read permission
        success = PermissionService.revoke_workflow_permission(workflow.id, 2, "read")
        assert success is True
        
        # Should still have write but not read
        assert PermissionService.check_read_permission(2, workflow.id) is False
        assert PermissionService.check_write_permission(2, workflow.id) is True

    def test_get_user_workflow_permissions(self):
        """Test getting all permissions for a user on a workflow"""
        workflow_data = WorkflowCreate(name="User Permissions Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Grant multiple permissions
        PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        PermissionService.grant_workflow_permission(workflow.id, 2, "write")
        
        permissions = PermissionService.get_user_workflow_permissions(2, workflow.id)
        assert "read" in permissions
        assert "write" in permissions

    def test_execute_permission_requires_read_access(self):
        """Test that execute permission requires read access"""
        workflow_data = WorkflowCreate(name="Execute Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Grant execute permission without read
        PermissionService.grant_workflow_permission(workflow.id, 2, "execute")
        
        # Should not have execute permission without read access
        assert PermissionService.check_execute_permission(2, workflow.id) is False
        
        # Grant read permission
        PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        
        # Now should have execute permission
        assert PermissionService.check_execute_permission(2, workflow.id) is True

    def test_api_permission_enforcement(self):
        """Test that API endpoints enforce permissions"""
        # Create workflow owned by user 1
        workflow_data = WorkflowCreate(name="API Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # User 2 should not be able to access workflow
        response = client.get(f"/api/workflows/{workflow.id}?user_id=2")
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
        
        # Grant read permission
        PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        
        # Now user 2 should be able to access
        response = client.get(f"/api/workflows/{workflow.id}?user_id=2")
        assert response.status_code == 200

    def test_workflow_execution_permission_enforcement(self):
        """Test that workflow execution enforces permissions"""
        workflow_data = WorkflowCreate(name="Execution Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # User 2 should not be able to execute workflow
        response = client.post(f"/api/workflows/{workflow.id}/execute", json={
            "user_id": 2,
            "parameters": {}
        })
        assert response.status_code == 403
        
        # Grant execute permission and read access
        PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        PermissionService.grant_workflow_permission(workflow.id, 2, "execute")
        
        # Now should be able to execute
        response = client.post(f"/api/workflows/{workflow.id}/execute", json={
            "user_id": 2,
            "parameters": {}
        })
        assert response.status_code == 200

    def test_get_workflow_users_with_permissions(self):
        """Test getting all users with permissions for a workflow"""
        workflow_data = WorkflowCreate(name="Users Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Grant permissions to different users
        PermissionService.grant_workflow_permission(workflow.id, 2, "read")
        PermissionService.grant_workflow_permission(workflow.id, 2, "write")
        
        # Create another user and grant permission
        test_user = User(
            id=4,
            email="test2@example.com",
            username="testuser2",
            password="test123",
            roles=[]
        )
        users_db.append(test_user)
        
        PermissionService.grant_workflow_permission(workflow.id, 4, "read")
        
        users_with_perms = PermissionService.get_workflow_users_with_permissions(workflow.id)
        
        assert 2 in users_with_perms
        assert 4 in users_with_perms
        assert "read" in users_with_perms[2]
        assert "write" in users_with_perms[2]
        assert "read" in users_with_perms[4]

    def test_invalid_permission_grant(self):
        """Test that invalid permissions cannot be granted"""
        workflow_data = WorkflowCreate(name="Invalid Permission Test", owner_id=1)
        workflow = WorkflowService.create_workflow(workflow_data)
        
        # Try to grant invalid permission
        success = PermissionService.grant_workflow_permission(workflow.id, 2, "invalid_permission")
        assert success is False
