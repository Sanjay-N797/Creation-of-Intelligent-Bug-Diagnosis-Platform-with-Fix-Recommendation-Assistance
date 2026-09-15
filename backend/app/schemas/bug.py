import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Chat Schemas
class ChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1)

class ChatMessageResponse(BaseModel):
    id: int
    bug_id: int
    sender: str
    message: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Bug Schemas
class BugBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    stack_trace: Optional[str] = Field(default="", alias="stackTrace")
    log_file_name: Optional[str] = Field(default="", alias="logFileName")
    log_content: Optional[str] = Field(default="", alias="logContent")
    category: Optional[str] = "Auto-detect"
    severity: Optional[str] = "Medium"
    priority: Optional[str] = "P3"

class BugCreate(BugBase):
    clarifications: Optional[Dict[str, str]] = None

    class Config:
        populate_by_name = True

class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stack_trace: Optional[str] = None
    log_file_name: Optional[str] = None
    log_content: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = None

class BugResolveRequest(BaseModel):
    root_cause: str = Field(..., alias="rootCause")
    resolution: str = Field(..., alias="resolution")
    resolution_notes: Optional[str] = Field(default="", alias="resolutionNotes")

    class Config:
        populate_by_name = True

class AnalysisResultSchema(BaseModel):
    triage: Dict[str, Any]
    logAnalysis: Dict[str, Any]
    rootCause: Dict[str, Any]
    duplicate: Dict[str, Any]
    ragRetrieval: Optional[Dict[str, Any]] = None
    remediation: Dict[str, Any]

class BugResponse(BaseModel):
    id: int
    bug_code: str = Field(..., alias="id")
    db_id: int = Field(..., alias="dbId")
    title: str
    description: Optional[str] = ""
    stack_trace: Optional[str] = Field(default="", alias="stackTrace")
    log_file_name: Optional[str] = Field(default="", alias="logFileName")
    log_content: Optional[str] = Field(default="", alias="logContent")
    category: str
    severity: str
    priority: str
    status: str
    root_cause: Optional[str] = Field(default=None, alias="rootCause")
    resolution: Optional[str] = None
    resolution_notes: Optional[str] = Field(default=None, alias="resolutionNotes")
    date_submitted: Optional[str] = Field(default=None, alias="dateSubmitted")
    date_resolved: Optional[str] = Field(default=None, alias="dateResolved")
    analysis_results: Optional[Dict[str, Any]] = Field(default=None, alias="analysisResults")

    class Config:
        populate_by_name = True
        from_attributes = True

class StatsResponse(BaseModel):
    total: int
    resolved: int
    open: int
    inProgress: int = 0
    severityCounts: Dict[str, int]
    categoryCounts: Dict[str, int]
    avgResolutionDays: str
    resolutionRate: str
    recentBugs: Optional[List[Dict[str, Any]]] = None

# Code Review Schemas
class CodeReviewRequest(BaseModel):
    code: str = Field(..., min_length=1)

class CodeReviewResponse(BaseModel):
    agent: str
    icon: str
    score: int
    grade: str
    findings: List[Dict[str, Any]]
    totalIssues: int
    categoryCounts: Dict[str, int]
    summary: str
    refactoredCode: Optional[str] = None

# New Feature Schemas
class AutoFixRequest(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""
    stack_trace: Optional[str] = Field(default="", alias="stackTrace")
    log_content: Optional[str] = Field(default="", alias="logContent")
    category: Optional[str] = "General"

    class Config:
        populate_by_name = True

class VerifyFixRequest(BaseModel):
    fixed_code: str = Field(..., alias="fixedCode")
    language: Optional[str] = "python"
    original_code: Optional[str] = Field(default="", alias="originalCode")

    class Config:
        populate_by_name = True

class TestGenRequest(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""
    stack_trace: Optional[str] = Field(default="", alias="stackTrace")
    language: Optional[str] = "python"

    class Config:
        populate_by_name = True

class SecurityScanRequest(BaseModel):
    code: str = Field(..., min_length=1)
    title: Optional[str] = ""

class PriorityScoreRequest(BaseModel):
    severity: str = "Medium"
    category: Optional[str] = "General"
    title: Optional[str] = ""
    description: Optional[str] = ""
    stack_trace: Optional[str] = Field(default="", alias="stackTrace")

    class Config:
        populate_by_name = True


