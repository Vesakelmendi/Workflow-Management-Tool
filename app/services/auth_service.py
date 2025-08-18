from typing import List, Optional
from ..models.user import User, UserCreate, UserResponse
from ..models.role import Role


# In-memory storage
users_db: List[User] = []
roles_db: List[Role] = [
    Role(id=1, name="admin", description="Administrator role", permissions=["read", "write", "execute", "admin"]),
    Role(id=2, name="user", description="Regular user role", permissions=["read", "write"]),
    Role(id=3, name="viewer", description="Read-only user role", permissions=["read"])
]

# Initialize with a default admin user
admin_role = roles_db[0]
default_admin = User(
    id=1,
    email="admin@example.com",
    username="admin",
    password="admin123",  # In real app, this would be hashed
    roles=[admin_role]
)
users_db.append(default_admin)


class AuthService:
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserResponse]:
        """Authenticate user by username and password"""
        user = next((u for u in users_db if u.username == username and u.password == password), None)
        if user:
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                roles=user.roles
            )
        return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        return next((u for u in users_db if u.id == user_id), None)

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        return next((u for u in users_db if u.username == username), None)

    @staticmethod
    def create_user(user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        # Check if user already exists
        if any(u.username == user_data.username or u.email == user_data.email for u in users_db):
            raise ValueError("User with this username or email already exists")
        
        # Assign default user role
        default_role = next((r for r in roles_db if r.name == "user"), roles_db[1])
        
        new_user = User(
            id=len(users_db) + 1,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,  # In real app, hash this
            roles=[default_role]
        )
        
        users_db.append(new_user)
        
        return UserResponse(
            id=new_user.id,
            email=new_user.email,
            username=new_user.username,
            roles=new_user.roles
        )

    @staticmethod
    def validate_user_role(user_id: int, required_permission: str) -> bool:
        """Check if user has required permission"""
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False
        
        for role in user.roles:
            if required_permission in role.permissions:
                return True
        return False

    @staticmethod
    def get_user_permissions(user_id: int) -> List[str]:
        """Get all permissions for a user"""
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return []
        
        permissions = set()
        for role in user.roles:
            permissions.update(role.permissions)
        return list(permissions)

    @staticmethod
    def assign_role_to_user(user_id: int, role_id: int) -> bool:
        """Assign a role to a user"""
        user = AuthService.get_user_by_id(user_id)
        role = next((r for r in roles_db if r.id == role_id), None)
        
        if user and role and role not in user.roles:
            user.roles.append(role)
            return True
        return False
