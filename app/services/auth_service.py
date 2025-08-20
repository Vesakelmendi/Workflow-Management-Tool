from typing import List, Optional
from ..models.user import User, UserCreate, UserResponse
from ..models.role import Role

# In-memory storage
users_db: List[User] = []
roles_db: List[Role] = [
    Role(id=1, name="Admin", description="Administrator role", permissions=["read", "write", "execute", "admin"]),
    Role(id=2, name="Analyst", description="Data analyst role", permissions=["read", "write"]),
    Role(id=3, name="Category Manager", description="Category management role", permissions=["read", "write"]),
    Role(id=4, name="Basic", description="Basic user role", permissions=["read"])
]

# Default admin user
admin_role = roles_db[0]
default_admin = User(
    id=1,
    email="admin@example.com",
    username="admin",
    password="admin123",
    roles=[admin_role]
)
users_db.append(default_admin)


# Auth Service 
class AuthService:

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserResponse]:
        """Authenticate user by username and password"""
        for u in users_db:
            if u.username == username and u.password == password:
                return UserResponse(
                    id=u.id,
                    email=u.email,
                    username=u.username,
                    roles=u.roles
                )
        return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID"""
        return next((u for u in users_db if u.id == user_id), None)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        return next((u for u in users_db if u.email == email), None)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Simple password verification"""
        return password == hashed_password

    @staticmethod
    def create_user(user_data: UserCreate) -> UserResponse:
        if any(u.username == user_data.username or u.email == user_data.email for u in users_db):
            raise ValueError("User with this username or email already exists")

        default_role = next((r for r in roles_db if r.name == "Basic"), roles_db[3])

        new_user = User(
            id=len(users_db) + 1,
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
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
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False
        return any(required_permission in role.permissions for role in user.roles)

    @staticmethod
    def get_user_permissions(user_id: int) -> List[str]:
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return []
        permissions = set()
        for role in user.roles:
            permissions.update(role.permissions)
        return list(permissions)

    @staticmethod
    def assign_role_to_user(user_id: int, role_id: int) -> bool:
        user = AuthService.get_user_by_id(user_id)
        role = next((r for r in roles_db if r.id == role_id), None)
        if user and role and role not in user.roles:
            user.roles.append(role)
            return True
        return False
