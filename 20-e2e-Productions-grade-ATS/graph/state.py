from typing import TypedDict, Optional, Dict, Any

# --- UPDATED GRAPH STATE ---
class GraphState(TypedDict):
    """
    Represents the state of the candidate processing pipeline.
    """
    # --- INPUTS ---
    file_name: str
    resume_markdown: str  
    job_description: str  
    
    # --- INTERMEDIATE OUTPUTS ---
    extracted_profile: Optional[Dict[str, Any]]
    
    # --- FINAL OUTPUTS ---
    evaluation_score: Optional[int]
    evaluation_reasoning: Optional[str]
    final_status: str
    
    # --- MISSING FIELD ADDED HERE ---
    evaluation_details: Optional[Dict[str, Any]]  # <--- This was missing!
    edge_case_log: Optional[str] # New field
    email_draft: Optional[str] # <--- Add this
    email_draft: Optional[Dict[str, str]]
    email_sent: Optional[bool] # New field to track sending success
    form_email: Optional[str] 
    
    extracted_profile: Optional[Dict[str, Any]]