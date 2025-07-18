from pydantic import BaseModel, Field, EmailStr

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=32, description="Unique username (case-insensitive)")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Account password, min 6 characters")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """User login request schema."""
    username: str = Field(..., min_length=3, max_length=32, description="Your username")
    password: str = Field(..., min_length=6, description="Your password")

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    """Public user info schema."""
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    """JWT access token schema."""
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field("bearer", description="Token type (always bearer)")
