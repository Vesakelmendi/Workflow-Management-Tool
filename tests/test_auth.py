import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.auth_service import AuthService, users_db, roles_db
from app.models.user import User, UserCreate
from app.models.role import Role

client = TestClient(app)


class TestAuthentication:
    def setup_method(self):
        """Reset test data before each test"""
        # Clear users except default admin
        users_db.clear()
        admin_role = next((r for r in roles_db if r.name == "admin"), None)
        if admin_role:
            default_admin = User(
                id=1,
                email="admin@example.com",
                username="admin",
                password="admin123",
                roles=[admin_role]
            )
            users_db.append(default_admin)

    def test_authenticate_valid_user(self):
        """Test authentication with valid credentials"""
        response = client.post("/api/authenticate", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == "admin"
        assert data["user"]["email"] == "admin@example.com"
        assert len(data["user"]["roles"]) > 0

    def test_authenticate_invalid_username(self):
        """Test authentication with invalid username"""
        response = client.post("/api/authenticate", json={
            "username": "nonexistent",
            "password": "admin123"
        })
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_authenticate_invalid_password(self):
        """Test authentication with invalid password"""
        response = client.post("/api/authenticate", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_authenticate_missing_fields(self):
        """Test authentication with missing fields"""
        response = client.post("/api/authenticate", json={
            "username": "admin"
            # Missing password
        })
        
        assert response.status_code == 422  # Validation error

    def test_auth_service_create_user(self):
        """Test creating a new user through AuthService"""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        user_response = AuthService.create_user(user_data)
        
        assert user_response.username == "testuser"
        assert user_response.email == "test@example.com"
        assert len(user_response.roles) > 0
        assert user_response.roles[0].name == "user"

    def test_auth_service_duplicate_user(self):
        """Test creating a user with duplicate username"""
        user_data = UserCreate(
            email="admin@example.com",
            username="admin",
            password="newpass"
        )
        
        with pytest.raises(ValueError, match="User with this username or email already exists"):
            AuthService.create_user(user_data)

    def test_auth_service_validate_user_role(self):
        """Test role validation"""
        # Admin should have admin permission
        assert AuthService.validate_user_role(1, "admin") is True
        
        # Admin should have read permission
        assert AuthService.validate_user_role(1, "read") is True
        
        # Admin should not have a non-existent permission
        assert AuthService.validate_user_role(1, "nonexistent") is False
        
        # Non-existent user should have no permissions
        assert AuthService.validate_user_role(999, "read") is False

    def test_auth_service_get_user_permissions(self):
        """Test getting user permissions"""
        permissions = AuthService.get_user_permissions(1)
        assert "read" in permissions
        assert "write" in permissions
        assert "execute" in permissions
        assert "admin" in permissions

    def test_auth_service_assign_role(self):
        """Test assigning a role to a user"""
        # Create a test user
        user_data = UserCreate(
            email="test2@example.com",
            username="testuser2",
            password="testpass123"
        )
        user_response = AuthService.create_user(user_data)
        
        # Get the admin role
        admin_role = next((r for r in roles_db if r.name == "admin"), None)
        assert admin_role is not None
        
        # Assign admin role to user
        success = AuthService.assign_role_to_user(user_response.id, admin_role.id)
        assert success is True
        
        # Verify user now has admin permissions
        assert AuthService.validate_user_role(user_response.id, "admin") is True
