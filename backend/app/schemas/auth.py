from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)
    remember_me: bool = False


class MeResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    roles: list[str]