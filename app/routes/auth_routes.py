from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional


# router = APIRouter(prefix="/api", tags=["authentication"])

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    roles: List[str]

class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str

class LoginResponse(BaseModel):
    success: bool = True
    user: UserResponse
    message: str = "Authentication successful"

# -----------------------------------------------------
# A simple in-memory list of users to act as our database.
USERS_DB = [
    {
        "id": "u1",
        "username": "John",
        "email": "john@example.com",
        "password": "pass123", # In a real app, this would be a hashed password
        "roles": ["Admin", "Analyst"]
    },
    {
        "id": "u2",
        "username": "Alice",
        "email": "alice@example.com",
        "password": "secret",
        "roles": ["Basic"]
    },
]
# -----------------------------------------------------

# @router.post("/authenticate", response_model=LoginResponse)
# async def authenticate(login_data: LoginRequest):
#     """Authenticate user with username and password"""
#     try:
#         user = AuthService.authenticate_user(login_data.username, login_data.password)
        
#         if user:
#             return LoginResponse(
#                 success=True,
#                 user=user,
#                 message="Authentication successful"
#             )
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid username or password"
#             )
    
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Authentication failed: {str(e)}"
#         )

class AuthService:
    """
    Handles all authentication-related logic.
    [cite_start]This separation makes the code testable and reusable[cite: 107, 111].
    """
    @staticmethod
    def authenticate_user(username: Optional[str], email: Optional[str], password: str) -> Optional[UserResponse]:
        """
        Finds a user by username or email and verifies their password.
        Returns the user data as a UserResponse object or None if authentication fails.
        """
        if not username and not email:
            return None # Must provide either username or email

        for user_data in USERS_DB:
            # Check if the provided username or email matches the current user in the loop
            user_found = (username and user_data["username"] == username) or \
                         (email and user_data["email"] == email)

            if user_found:
                # If the user is found, check the password
                if user_data["password"] == password:
                    # Return the user data, automatically validated by the Pydantic model
                    return UserResponse(**user_data)
                else:
                    # Found the user but the password was wrong
                    return None
        
        # If the loop finishes, no user was found with that email/username
        return None

# --------------------------------------------------------------------------
# 4. API ROUTER: Defines the API endpoints
# --------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["authentication"])

@router.post("/authenticate", response_model=LoginResponse)
async def authenticate(login_data: LoginRequest):
    """
    Authenticates a user with their username/email and password.
    """
    try:
        user = AuthService.authenticate_user(
            username=login_data.username,
            email=login_data.email,
            password=login_data.password
        )
        
        if user:
            return LoginResponse(user=user)
        else:
            # If the service returns None, authentication failed.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    
    except Exception as e:
        # A catch-all for any other unexpected errors during the process.
        # This makes the endpoint more robust.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
