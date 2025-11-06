from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from jose import jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.services.github_service import GitHubService
from src.services.gemini_service import GeminiService
from src.services.langchain_service import LangChainService
from src.utils.helpers import extract_repo_info, validate_github_url
from src.core.config import settings
from src.db import models
from src import schemas

router = APIRouter()

# Initialize services
github_service = GitHubService()
gemini_service = GeminiService()
langchain_service = LangChainService()

# Initialize password context once
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)  # 30 min expiry
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/auth/register", response_model=schemas.Token)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
            
        # Create user
        db_user = models.User(
            email=user.email,
            hashed_password=pwd_context.hash(user.password),
            github_username=user.github_username
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Generate token
        access_token = create_access_token(
            data={"sub": db_user.email, "id": db_user.id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": db_user.id,
            "email": db_user.email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    # Find user by email
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not pwd_context.verify(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }

@router.get("/admin/db-status")
async def check_db_status(db: Session = Depends(get_db)):
    """Check database connection and tables"""
    try:
        from sqlalchemy import text
        
        # Try to execute a simple query
        result = db.execute(text("SELECT 1")).scalar()
        
        # Get table information
        tables = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).fetchall()
        
        return {
            "status": "connected",
            "tables": [table[0] for table in tables],
            "test_query_result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.post("/projects", response_model=schemas.Project)
async def create_project(
    project: schemas.ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    try:
        # Validate GitHub URL
        if not validate_github_url(project.github_repo):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
            
        # Create project
        db_project = models.Project(
            name=project.name,
            description=project.description,
            github_repo=project.github_repo,
            owner_id=current_user["id"]
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        return schemas.Project(
            id=db_project.id,
            name=db_project.name,
            description=db_project.description,
            github_repo=db_project.github_repo,
            owner_id=db_project.owner_id,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects/{project_id}/analyses", response_model=List[schemas.Analysis])
async def get_project_analyses(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all analyses for a project"""
    try:
        # Check if project exists and belongs to user
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.owner_id == current_user["id"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Get all analyses
        analyses = db.query(models.CodeAnalysis).filter(
            models.CodeAnalysis.project_id == project_id
        ).all()
        
        return [
            schemas.Analysis(
                id=analysis.id,
                type=analysis.analysis_type,
                result=analysis.analysis_result,
                created_at=str(analysis.created_at)
            )
            for analysis in analyses
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/repos", response_model=schemas.GitHubRepoList)
async def get_user_repos(
    username: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all repositories for a GitHub user"""
    try:
        repos = github_service.get_user_repos(username)
        return schemas.GitHubRepoList(repos=repos)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repo/content", response_model=schemas.RepoContentResponse)
async def get_repository_content(
    repo_url: str,
    path: str = "",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content of a GitHub repository"""
    try:
        if not validate_github_url(repo_url):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
        repo_info = extract_repo_info(repo_url)
        content = github_service.get_repo_content(repo_info["full_name"], path)
        return schemas.RepoContentResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze/code-review", response_model=schemas.CodeReviewResponse)
async def analyze_code_review(
    analysis: schemas.AnalysisCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform AI-powered code review"""
    try:
        # Check if project exists and belongs to user
        project = db.query(models.Project).filter(
            models.Project.id == analysis.project_id,
            models.Project.owner_id == current_user["id"]
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Generate the review
        review = gemini_service.generate_code_review(analysis.code, analysis.context or "")
        
        # Store the analysis in the database
        db_analysis = models.CodeAnalysis(
            project_id=analysis.project_id,
            analysis_type="code_review",
            input_code=analysis.code,
            analysis_result=review
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        return schemas.CodeReviewResponse(
            review=review,
            analysis_id=db_analysis.id,
            created_at=str(db_analysis.created_at)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze/documentation", response_model=schemas.DocumentationResponse)
async def generate_documentation(
    request: schemas.CodeAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate documentation for code"""
    try:
        if not request.code:
            raise HTTPException(status_code=400, detail="Code content is required")
        
        documentation = gemini_service.generate_documentation(request.code)
        return schemas.DocumentationResponse(documentation=documentation)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze/bug-detection", response_model=schemas.BugDetectionResponse)
async def detect_bugs(
    request: schemas.CodeAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect bugs in code"""
    try:
        if not request.code:
            raise HTTPException(status_code=400, detail="Code content is required")
        
        bugs = gemini_service.detect_bugs(request.code)
        return schemas.BugDetectionResponse(bugs=bugs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/repo/analyze-complete", response_model=schemas.RepoAnalysisResponse)
async def analyze_complete_repository(
    request: schemas.RepoAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform complete analysis of a repository"""
    try:
        if not validate_github_url(request.repo_url):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
        repo_info = extract_repo_info(request.repo_url)
        
        # Configuration
        MAX_FILES = 100
        MAX_FILE_SIZE = 50_000  # characters
        SUPPORTED_EXTENSIONS = ('.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.jsx', '.tsx')
        
        files_content = []
        skipped_files = []
        
        def get_all_files(repo_full_name: str, path: str = "", depth: int = 0):
            # Prevent infinite recursion
            if depth > 10:
                return
                
            try:
                contents = github_service.get_repo_content(repo_full_name, path)
            except Exception as e:
                print(f"Error accessing path {path}: {str(e)}")
                return
            
            for item in contents:
                # Stop if we've hit file limit
                if len(files_content) >= MAX_FILES:
                    return
                    
                if item["type"] == "file" and item["name"].endswith(SUPPORTED_EXTENSIONS):
                    try:
                        # Skip large files
                        if item.get("size", 0) > MAX_FILE_SIZE:
                            skipped_files.append(f"{item['path']} (too large)")
                            continue
                            
                        content = github_service.get_file_content(repo_full_name, item["path"])
                        
                        # Skip if content is too large after fetching
                        if len(content) > MAX_FILE_SIZE:
                            skipped_files.append(f"{item['path']} (too large)")
                            continue
                            
                        files_content.append(schemas.FileContent(
                            name=item["name"],
                            path=item["path"],
                            content=content,
                            language=item["name"].split('.')[-1],
                            repo=repo_full_name
                        ))
                    except Exception as e:
                        skipped_files.append(f"{item['path']} (error: {str(e)})")
                        
                elif item["type"] == "dir":
                    get_all_files(repo_full_name, item["path"], depth + 1)
        
        get_all_files(repo_info["full_name"])

        if not files_content:
            return schemas.RepoAnalysisResponse(
                overall_analysis="No supported source files found in repository.",
                files_analyzed=0,
                repo_info=repo_info
            )

        # Process with LangChain (if you're using vector store for Q&A later)
        documents = langchain_service.process_code_documents([f.dict() for f in files_content])
        langchain_service.create_vector_store(documents)

        # Create a structured summary of the codebase
        file_structure = {}
        for file in files_content:
            ext = file.language
            if ext not in file_structure:
                file_structure[ext] = []
            file_structure[ext].append(file.path)
        
        structure_summary = "\n".join([
            f"- {ext}: {len(files)} files" 
            for ext, files in file_structure.items()
        ])

        # Sample files intelligently (get diverse file types)
        sample_files = []
        for ext in file_structure.keys():
            ext_files = [f for f in files_content if f.language == ext]
            sample_files.extend(ext_files[:2])  # 2 files per language
        
        # Limit to 10 files total for analysis
        sample_files = sample_files[:10]
        
        # Create context for LLM
        code_context = "\n\n---\n\n".join([
            f"File: {f.path}\nLanguage: {f.language}\n\n{f.content[:2000]}"  # First 2000 chars
            for f in sample_files
        ])

        # Generate structured analysis
        analysis_prompt = f"""
Analyze this repository: {repo_info['full_name']}

Repository Structure:
{structure_summary}

Total files analyzed: {len(files_content)}
Sample files provided: {len(sample_files)}

Sample Code:
{code_context}

Provide a CONCISE analysis with the following structure:

## 1. Overview
Brief description of the project's purpose and tech stack.

## 2. Code Quality (3-4 bullet points)
- Key strengths
- Main areas for improvement

## 3. Architecture (3-4 bullet points)
- Overall structure
- Design patterns used
- Potential issues

## 4. Security Concerns (2-3 bullet points)
- Critical security issues if any
- Recommendations

## 5. Quick Wins (3-4 actionable items)
- Immediate improvements that can be made

Keep each section concise and actionable. Use bullet points, not paragraphs.
        """

        overall_analysis = gemini_service.generate_code_review(
            code_context,
            analysis_prompt,
        )
        
        # Add metadata to response
        analysis_with_metadata = f"""# Repository Analysis: {repo_info['full_name']}

**Files Analyzed:** {len(files_content)} files
**Files Skipped:** {len(skipped_files)} files
**Sample Files Used:** {len(sample_files)} files

{overall_analysis}

---
### Skipped Files
{chr(10).join(skipped_files[:10]) if skipped_files else 'None'}
"""
        
        return schemas.RepoAnalysisResponse(
            overall_analysis=analysis_with_metadata,
            files_analyzed=len(files_content),
            repo_info=repo_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query/codebase", response_model=schemas.CodebaseQueryResponse)
async def query_codebase(
    request: schemas.CodebaseQuery,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query the codebase using natural language"""
    try:
        if not request.question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        response = langchain_service.query_codebase(request.question)
        return schemas.CodebaseQueryResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/issues/create", response_model=schemas.GitHubIssueResponse)
async def create_github_issue(
    request: schemas.GitHubIssueCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a GitHub issue"""
    try:
        if not validate_github_url(request.repo_url):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
        
        repo_info = extract_repo_info(request.repo_url)
        issue = github_service.create_issue(repo_info["full_name"], request.title, request.body)
        
        return schemas.GitHubIssueResponse(issue=issue)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/db-status", response_model=schemas.DBStatus)
async def db_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin endpoint: show simple row counts for core tables."""
    try:
        users = db.query(models.User).count()
        projects = db.query(models.Project).count()
        analyses = db.query(models.CodeAnalysis).count()
        return schemas.DBStatus(tables={
            "users": users,
            "projects": projects,
            "analyses": analyses
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/projects", response_model=List[schemas.Project])
async def get_user_projects(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user"""
    try:
        projects = db.query(models.Project).filter(
            models.Project.owner_id == current_user["id"]
        ).order_by(models.Project.created_at.desc()).all()
        
        return [
            schemas.Project(
                id=project.id,
                name=project.name,
                description=project.description,
                github_repo_url=project.github_repo_url,
                user_id=project.owner_id,
                created_at=str(project.created_at),
                updated_at=str(project.updated_at)
            )
            for project in projects
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}", response_model=schemas.Project)
async def get_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single project by ID"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.owner_id == current_user["id"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return schemas.Project(
            id=project.id,
            name=project.name,
            description=project.description,
            github_repo_url=project.github_repo_url,
            user_id=project.owner_id,
            created_at=str(project.created_at),
            updated_at=str(project.updated_at)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    try:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.owner_id == current_user["id"]
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        db.delete(project)
        db.commit()
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))