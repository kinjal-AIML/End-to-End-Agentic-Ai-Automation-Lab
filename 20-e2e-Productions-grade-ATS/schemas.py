from pydantic import BaseModel, Field
from typing import List, Optional
from typing import Literal

class SkillWeight(BaseModel):
    skill: str = Field(description="Name of the skill, e.g., 'FastAPI'")
    importance: Literal["CRITICAL", "HIGH", "MEDIUM", "NICE_TO_HAVE"] = Field(
        description="CRITICAL=Auto Reject if missing. HIGH=Major Score Impact."
    )
    weight_points: int = Field(description="Points to deduct if missing. Critical=25, High=15, Medium=5, Nice=2")

class JobScoringRubric(BaseModel):
    """
    The Master Instruction set for the Evaluator Agent.
    """
    role_title: str
    summary_for_evaluator: str = Field(description="Short context for the AI Evaluator about what this role entails.")
    
    # The Marking Criteria
    skills_criteria: List[SkillWeight]
    
    min_years_experience: float
    requires_degree: bool = Field(description="True if a degree is strictly required")
    
    auto_reject_keywords: List[str] = Field(description="e.g. ['Recruiter', 'HR', 'Graphic Designer'] for a Dev role")

class Education(BaseModel):
    degree: str = Field(description="Degree name, e.g., B.Sc in Computer Science")
    institution: str = Field(description="University or College name")
    year: str = Field(description="Graduation year or range")

class Project(BaseModel):
    name: str = Field(description="Project title")
    description: str = Field(description="Brief summary of the project")
    tech_stack: List[str] = Field(description="List of tools/languages used in this project")

class CandidateProfile(BaseModel):
    """
    Structured extraction of a candidate's resume.
    """
    full_name: str = Field(description="Candidate's full name")
    email: str = Field(description="Email address")
    phone: Optional[str] = Field(description="Phone number if available")
    
    linkedin_url: Optional[str] = Field(description="LinkedIn profile URL")
    github_url: Optional[str] = Field(description="GitHub/Portfolio URL")
    
    total_years_experience: float = Field(description="Calculated total years of professional experience. 0 if fresh grad.")
    
    technical_skills: List[str] = Field(description="List of programming languages, frameworks, and tools")
    soft_skills: List[str] = Field(description="List of interpersonal skills")
    
    education_details: List[Education]
    project_details: List[Project]
    
    summary: str = Field(description="A concise 2-sentence professional summary generated from the resume.")


# --- Add this to app/schemas.py ---

class ScoringResult(BaseModel):
    """
    The AI's final evaluation of the candidate.
    """
    score: int = Field(description="Final score between 0-100 based on the rubric.")
    decision: str = Field(description="One of: SHORTLISTED, REVIEW, REJECTED, MISMATCH")
    
    matching_skills: List[str] = Field(description="Skills from the JD that the candidate possesses.")
    missing_critical_skills: List[str] = Field(description="Critical 'Must Have' skills missing from the profile.")
    
    reasoning: str = Field(description="A brief justification for the score (max 3 sentences).")



# ---JD Rubric---
class SkillWeight(BaseModel):
    skill: str = Field(description="Name of the skill, e.g., 'FastAPI'")
    importance: Literal["CRITICAL", "HIGH", "MEDIUM", "NICE_TO_HAVE"] = Field(
        description="CRITICAL=Auto Reject if missing. HIGH=Major Score Impact."
    )
    weight_points: int = Field(description="Points to deduct if missing. Critical=25, High=15, Medium=5, Nice=2")

class JobScoringRubric(BaseModel):
    """
    The Master Instruction set for the Evaluator Agent.
    """
    role_title: str
    summary_for_evaluator: str = Field(description="Short context for the AI Evaluator about what this role entails.")
    
    # The Marking Criteria
    skills_criteria: List[SkillWeight]
    
    min_years_experience: float
    requires_degree: bool = Field(description="True if a degree is strictly required")
    
    auto_reject_keywords: List[str] = Field(description="e.g. ['Recruiter', 'HR', 'Graphic Designer'] for a Dev role")

# In app/schemas.py

class EmailDraft(BaseModel):
    subject: str = Field(description="A professional, concise subject line.")
    body: str = Field(description="The main content of the email (HTML or Text).")
    signature: str = Field(description="The closing sign-off (e.g., 'Best regards, The AI Team').")