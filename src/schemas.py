from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    github_username: str | None = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    github_repo: str

class Project(ProjectCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class AnalysisCreate(BaseModel):
    code: str
    context: str | None = None
    project_id: int

class Analysis(BaseModel):
    id: int
    type: str
    result: str
    created_at: str
    class Config:
        from_attributes = True