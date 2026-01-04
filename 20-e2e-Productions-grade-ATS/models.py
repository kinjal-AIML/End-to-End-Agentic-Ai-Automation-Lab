import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON, Text

# --- ENUMS (Strict Value Control) ---
class JobStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"

class ApplicationStatus(str, Enum):
    PENDING = "PENDING"          # Uploaded, waiting for worker
    PROCESSING = "PROCESSING"    # LangGraph is running
    SHORTLISTED = "SHORTLISTED"  # Score > 75
    REVIEW = "REVIEW"            # Score 40-75 (Needs Human eyes)
    REJECTED = "REJECTED"        # Score < 40
    MISMATCH = "MISMATCH"        # Wrong Domain (Designer -> Python Role)
    ERROR = "ERROR"              # File corrupt / Empty

# --- BASE MODEL (The Foundation) ---
# Every table will inherit these fields automatically.
class BaseTable(SQLModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, 
        primary_key=True, 
        index=True, 
        nullable=False
    )
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.utcnow} # Auto-update timestamp on edit
    )

# --- TABLE 1: JOBS (The "Ground Truth") ---
class Job(BaseTable, table=True):
    __tablename__ = "jobs"

    title: str = Field(index=True, description="e.g. Python Intern")
    department: Optional[str] = Field(default="Engineering")
    
    # The raw text pasted by HR
    raw_description: str = Field(sa_column=Column(Text))
    
    # CRITICAL: The AI-generated Rubric. 
    # We use SQLAlchemy JSON type to store lists/dicts properly in Postgres.
    structured_rubric: Dict[str, Any] = Field(
        default={}, 
        sa_column=Column(JSON), 
        description="JSON containing must_haves, nice_to_haves, yoe"
    )
    
    status: JobStatus = Field(default=JobStatus.OPEN)
    
    # Relationship: One Job -> Many Applications
    applications: List["Application"] = Relationship(back_populates="job")


# --- TABLE 2: APPLICATIONS (The Candidates) ---
class Application(BaseTable, table=True):
    __tablename__ = "applications"

    # Foreign Key to link to Job
    job_id: uuid.UUID = Field(foreign_key="jobs.id", index=True)
    
    # File Details
    file_path: str = Field(description="Storage path e.g. /uploads/job_x/resume_y.pdf")
    file_name: str = Field(description="Original filename uploaded by user")
    
    # Phase 1 Output: The Markdown from LlamaParse
    parsed_markdown: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Phase 2 Output: Extraction (Name, Email, Skills)
    candidate_profile: Dict[str, Any] = Field(
        default={}, 
        sa_column=Column(JSON),
        description="AI extracted data: name, email, phone, skills list"
    )
    
    # Phase 3 Output: Scoring & Reasoning
    ai_evaluation: Dict[str, Any] = Field(
        default={}, 
        sa_column=Column(JSON),
        description="The detailed scoring breakdown, pros/cons"
    )
    
    score: int = Field(default=0, index=True, description="0-100 Score")
    status: ApplicationStatus = Field(default=ApplicationStatus.PENDING, index=True)
    
    # Robustness Logging
    edge_case_log: Optional[str] = Field(default=None, description="Logs if file was empty, encrypted, or weird format")
    
    # Relationship: Link back to Job
    job: Optional[Job] = Relationship(back_populates="applications")