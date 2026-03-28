"""
Pydantic schemas for the AI Resume Screener LangGraph pipeline.

This module defines two schema groups:
1. Extraction schemas (ResumeExtractionResult, JDExtractionResult) — rich structured
   representations of parsed documents, proven in notebooks/02_structured_extraction.ipynb.
2. Pipeline schemas (GapAnalysis, HiringRecommendation, ScreenerState) — used by the
   analysis and recommendation agents to produce the final output.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Extraction Schemas (Notebook 02 — proven via Groq structured output)
# =============================================================================

class ExperienceEntry(BaseModel):
    """A single professional role on a resume."""
    job_title: str = Field(description="The exact job title as it appears on the resume.")
    company: str = Field(description="The employer or organisation name.")
    duration: str = Field(description="The date range of the role, exactly as it appears (e.g., 'Jun 2022 - Present').")
    responsibilities: List[str] = Field(description="A list of key responsibilities or accomplishments for this role.")

class EducationEntry(BaseModel):
    """A single educational credential on a resume."""
    degree: str = Field(description="The degree or qualification obtained (e.g., 'B.Sc. Computer Science').")
    institution: str = Field(description="The name of the university or institution.")
    graduation_year: Optional[str] = Field(default=None, description="The year of graduation or expected graduation.")

class ResumeExtractionResult(BaseModel):
    """
    Structured extraction of a candidate's resume.
    Proven schema from notebooks/02_structured_extraction.ipynb.
    All fields map 1-to-1 with what the LLM can reliably extract.
    """
    candidate_name: str = Field(description="The full name of the candidate.")
    contact_email: Optional[str] = Field(default=None, description="The candidate's email address.")
    contact_phone: Optional[str] = Field(default=None, description="The candidate's phone number as it appears on the resume, e.g. '(267) 555-0142'.")
    professional_summary: str = Field(description="A concise summary of the candidate's professional background. Max 3–4 sentences.")
    total_years_of_experience: Optional[float] = Field(default=None,description="Total years of professional experience estimated by the LLM. Will be overridden by deterministic calculation from experience dates.")
    technical_skills: List[str] = Field(description="A flat list of all specific technical skills, tools, libraries, frameworks, and programming languages mentioned anywhere in the resume.")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills or professional competencies inferred from the resume (e.g., 'stakeholder communication', 'mentoring').")
    experience: List[ExperienceEntry] = Field(description="All professional roles, ordered from most recent to oldest.")
    education: List[EducationEntry] = Field(description="All educational credentials, ordered from highest to lowest degree.")
    certifications: List[str] = Field(default_factory=list, description="Professional certifications mentioned (e.g., 'AWS Certified Solutions Architect').")
    notable_projects: List[str] = Field(default_factory=list, description="High-level names or one-sentence descriptions of notable personal or professional projects.")

class JDExtractionResult(BaseModel):
    """
    Structured extraction of a Job Description.
    Focused on what the job *requires* — not a candidate's profile.
    """
    job_title: str = Field(description="The job title exactly as stated in the JD.")
    company_name: str = Field(description="The name of the hiring company. Return 'Unknown' if not specified.")
    required_technical_skills: List[str] = Field(description=(
        "A flat list of specific, atomic, named competencies that are explicitly required or strongly preferred. "
        "Each item must be a concrete, nameable skill — something a candidate could list on a resume or be tested on. "
        "RULE: Never include a category, group, or umbrella term — only its specific members. "
        "For example: if the JD says 'backend languages such as Go, Python, Rust', extract ['Go', 'Python', 'Rust'], NOT 'backend languages'. "
        "This rule applies universally: 'HR tools' → extract the named tools. 'marketing channels' → extract the named channels. "
        "Deduplicate: include each distinct skill exactly once."
    ))
    nice_to_have_skills: List[str] = Field(default_factory=list, description="Skills listed as 'nice to have', 'preferred', or 'bonus'.")
    required_years_of_experience: Optional[int] = Field(default=None, description="The minimum years of professional experience required. Return null if not specified.")
    minimum_education_level: Optional[str] = Field(default=None, description="The minimum degree required (e.g., 'Bachelor', 'Master', 'PhD'). Return null if not explicitly stated.")
    core_responsibilities: List[str] = Field(description="A list of 3-5 primary duties or responsibilities the candidate will be expected to perform.")
    domain_experience: List[str] = Field(default_factory=list, description="Specific industries or functional domains explicitly required as a background for the candidate (e.g., 'FinTech', 'Healthcare'). Extract ONLY from the job requirements section. Ignore company mission statements, 'about us' boilerplate, or DEI sections. If a domain appears as both an acronym and full name (e.g., 'AI' and 'Artificial Intelligence'), use only the full name once.")
    soft_skills: List[str] = Field(default_factory=list, description="Non-technical competencies mentioned (e.g., 'communication', 'leadership', 'agile').")


# =============================================================================
# Pipeline Intermediate & Output Schemas
# =============================================================================
class GapAnalysis(BaseModel):
    """Semantic comparison between the JD requirements and candidate skills."""
    matching_skills: List[str] = Field(description="Core hard skills from the JD that the candidate definitively possesses.")
    missing_skills: List[str] = Field(description="Core hard skills from the JD that the candidate definitively lacks.")
    transferable_skills: List[str] = Field(description="Skills mapping to JD requirements. FORMAT: 'CandidateSkill (maps to Requirement)'.")
    experience_gap: str = Field(description="A concise 1-sentence assessment of whether the candidate's years of experience meet the JD requirement.")
    match_score_raw: int = Field(ge=0, le=100, description="An internal 0-100 score representing the objective skill match before the final recommendation.")


class HiringRecommendation(BaseModel):
    """The final human-readable assessment and recommendation for the recruiter."""
    verdict: Literal["Strong Hire", "Hire", "Hold", "Reject"] = Field(description="The final categorical recommendation.")
    score: int = Field(ge=0, le=100, description="The final 0-100 match score.")
    executive_summary: str = Field(description="A 2-3 sentence recruiter-friendly summary explaining the core reason for the verdict.")
    red_flags: List[str] = Field(description="Critical missing skills or seniority mismatches. Empty list if none.")
    interview_focus_areas: List[str] = Field(description="2-3 specific areas the interviewer should probe based on the candidate's gaps or ambiguities.")


# =============================================================================
# LangGraph State Schema
# =============================================================================

class ScreenerState(BaseModel):
    """The state object passed between nodes in the LangGraph workflow."""
    jd_text: str = ""
    resume_text: str = ""
    calibration_mode: Literal["lenient", "standard", "strict"] = "standard"
    jd_skills: Optional[JDExtractionResult] = None
    resume_skills: Optional[ResumeExtractionResult] = None
    gap_analysis: Optional[GapAnalysis] = None
    final_recommendation: Optional[HiringRecommendation] = None
