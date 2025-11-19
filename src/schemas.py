from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")
class ApiResponse(GenericModel, Generic[T]):
    data: T
    message: Optional[str] = None
    
# --- User / Auth models -------------------------------------------------
class UserBase(BaseModel):
    email: EmailStr
    github_username: Optional[str] = None


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
    github_username: str


# --- Project / Analysis models -----------------------------------------
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    github_repo: str


class Project(ProjectCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class AnalysisCreate(BaseModel):
    code: str
    context: Optional[str] = None
    project_id: int


class Analysis(BaseModel):
    id: int
    type: str
    result: str
    created_at: str

    class Config:
        from_attributes = True


# --- GitHub / Repo related models -------------------------------------
class GitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    language: Optional[str] = None
    stargazers_count: int = 0
    forks_count: int = 0
    default_branch: str = "main"


class GitHubRepoList(BaseModel):
    repos: List[GitHubRepo]


class RepoContentItem(BaseModel):
    name: str
    path: str
    type: str
    size: int
    url: str
    sha: str


class RepoContentResponse(BaseModel):
    content: List[RepoContentItem]


class FileContent(BaseModel):
    name: str
    path: str
    content: str
    language: Optional[str] = None
    repo: Optional[str] = None


class RepoInfo(BaseModel):
    owner: str
    repo: str
    full_name: str


class RepoAnalysisResponse(BaseModel):
    overall_analysis: str
    files_analyzed: int
    repo_info: RepoInfo


class RepoAnalysisRequest(BaseModel):
    repo_url: str
    # Optional: limit file types to analyze (e.g. [".py", ".js"]). If omitted, default extensions are used.
    extensions: Optional[List[str]] = None


# --- AI analysis response models ---------------------------------------
class CodeReviewResponse(BaseModel):
    review: str
    analysis_id: int
    created_at: str


class DocumentationResponse(BaseModel):
    documentation: str


class BugDetectionResponse(BaseModel):
    bugs: str


class CodeAnalysisRequest(BaseModel):
    code: str
    context: Optional[str] = None


# --- Codebase query / vectorstore models -------------------------------
class CodebaseQuery(BaseModel):
    question: str


class CodebaseQueryResponse(BaseModel):
    response: Dict[str, Any]


# --- GitHub issue models -----------------------------------------------
class GitHubIssueCreate(BaseModel):
    repo_url: str
    title: str
    body: str


class GitHubIssueResponse(BaseModel):
    issue: Dict[str, Any]


# --- Admin / Misc -----------------------------------------------------
class DBStatus(BaseModel):
    tables: Dict[str, int]
