"""
LangGraph node functions for the AI Resume Screener pipeline.

Each node:
1. Loads its prompt from the prompts/ directory.
2. Calls the LLM via ChatGroq with .with_structured_output() — consistent with
   the pattern proven in notebooks/02_structured_extraction.ipynb.
3. Returns a partial state dict that LangGraph merges into the full ScreenerState.

Post-processing:
- Resume extraction: total_years_of_experience is overridden by the deterministic
  calculate_experience_years() function (math > LLM self-report).
- Resume extraction: soft_skills are normalized to lowercase.
"""
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from src.core.llm import get_llm
from src.schemas.models import (
    GapAnalysis,
    HiringRecommendation,
    JDExtractionResult,
    ResumeExtractionResult,
    ScreenerState,
)
from src.utils.experience import calculate_experience_years

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    """Read a prompt template file from the prompts/ directory."""
    path = _PROMPTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_jd_node(state: ScreenerState) -> dict:
    """
    Agent 1a — JD Extraction.
    Extracts structured requirements from the raw Job Description text.
    """
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(JDExtractionResult)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("extract_prompt.txt")),
        ("human", "Please extract the structured information from the following Job Description:\n\n{document_text}"),
    ])

    chain = prompt_template | structured_llm
    result: JDExtractionResult = chain.invoke({
        "document_type": "Job Description",
        "document_text": state.jd_text,
    })
    return {"jd_skills": result}


def extract_resume_node(state: ScreenerState) -> dict:
    """
    Agent 1b — Resume Extraction.
    Extracts structured skills and experience from the raw Candidate Resume text.
    Applies post-processing: deterministic experience calculation + soft skill normalisation.
    """
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ResumeExtractionResult)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("extract_prompt.txt")),
        ("human", "Please extract the structured information from the following Resume:\n\n{document_text}"),
    ])

    chain = prompt_template | structured_llm
    result: ResumeExtractionResult = chain.invoke({
        "document_type": "Resume",
        "document_text": state.resume_text,
    })

    # Post-processing: deterministic experience override and soft skill normalisation
    result.total_years_of_experience = calculate_experience_years(result.experience)
    result.soft_skills = [s.lower() for s in result.soft_skills]

    return {"resume_skills": result}


def analyze_gaps_node(state: ScreenerState) -> dict:
    """
    Agent 2 — Gap Analysis.
    Performs semantic comparison between JD requirements and candidate skills.
    """
    if not state.jd_skills or not state.resume_skills:
        raise ValueError("Cannot perform gap analysis: JD or Resume extraction results are missing.")

    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(GapAnalysis)

    jd = state.jd_skills
    resume = state.resume_skills

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("analyze_prompt.txt")),
        ("human", "Perform the gap analysis now."),
    ])

    chain = prompt_template | structured_llm
    result: GapAnalysis = chain.invoke({
        "jd_hard_skills": ", ".join(jd.required_technical_skills),
        "jd_soft_skills": ", ".join(jd.soft_skills),
        "jd_domains": ", ".join(jd.domain_experience),
        "jd_yoe": str(jd.required_years_of_experience or "Not specified"),
        "jd_education": str(jd.minimum_education_level or "Not specified"),
        "jd_responsibilities": ", ".join(jd.core_responsibilities),
        "resume_hard_skills": ", ".join(resume.technical_skills),
        "resume_soft_skills": ", ".join(resume.soft_skills),
        "resume_domains": ", ".join([e.job_title for e in resume.experience]),
        "resume_yoe": str(resume.total_years_of_experience),
    })
    return {"gap_analysis": result}


def generate_recommendation_node(state: ScreenerState) -> dict:
    """
    Agent 3 — Final Recommendation.
    Generates the human-readable hiring verdict, score, red flags, and interview areas.
    """
    if not state.gap_analysis:
        raise ValueError("Cannot generate recommendation: Gap analysis result is missing.")

    llm = get_llm(temperature=0.2)
    structured_llm = llm.with_structured_output(HiringRecommendation)

    ga = state.gap_analysis
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("recommend_prompt.txt")),
        ("human", "Generate the final hiring recommendation now."),
    ])

    chain = prompt_template | structured_llm
    result: HiringRecommendation = chain.invoke({
        "raw_score": ga.match_score_raw,
        "matching_skills": ", ".join(ga.matching_skills),
        "missing_skills": ", ".join(ga.missing_skills),
        "transferable_skills": ", ".join(ga.transferable_skills),
        "experience_gap": ga.experience_gap,
    })
    return {"final_recommendation": result}
