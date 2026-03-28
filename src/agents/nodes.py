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

# Domain-agnostic suffixes that signal a vague category label rather than a specific skill.
# Works across technical AND non-technical roles:
#   Technical: "backend languages", "cloud platforms", "web frameworks"
#   Non-technical: "HR tools", "marketing channels", "financial systems"
_CATEGORY_SUFFIXES = {
    "languages", "tools", "technologies", "platforms", "frameworks",
    "software", "systems", "methods", "methodologies", "channels",
    "processes", "skills", "competencies", "applications", "solutions",
}

# Known compound disciplines that end in a grouping suffix but ARE specific skills.
# A short allowlist to prevent false positives in _is_category_label().
# Add entries here if a legitimate skill is incorrectly filtered.
_KNOWN_SPECIFIC_SKILLS = {
    "distributed systems",
    "operating systems",
    "recommender systems",
    "database systems",
    "embedded systems",
    "information systems",
    "control systems",
    "design systems",  # UX/UI discipline
    "expert systems",
    "agile methodologies",
    "lean methodologies",
}

def _is_category_label(skill: str) -> bool:
    """
    Returns True if the skill string looks like a vague category label
    rather than a specific, atomic skill.

    Detection logic: the last word of a multi-word phrase is a known
    'grouping noun' (e.g. 'backend languages', 'HR tools', 'cloud platforms').
    Single-word skills (e.g. 'Python', 'Docker') are never categories.
    Known compound disciplines in _KNOWN_SPECIFIC_SKILLS are always kept.
    """
    normalized = skill.lower().strip()
    if normalized in _KNOWN_SPECIFIC_SKILLS:
        return False  # Always keep known compound disciplines
    words = normalized.split()
    return len(words) > 1 and words[-1] in _CATEGORY_SUFFIXES

def _normalize_jd(result: "JDExtractionResult") -> "JDExtractionResult":
    """
    Deterministic post-processing for JD extraction results.

    Applies two normalization passes:
    1. Remove vague category labels from required_technical_skills if at least
       one specific skill is also present. Uses domain-agnostic suffix detection
       so it works for both technical and non-technical roles.
    2. Deduplicate domain_experience by removing items that are a substring of
       another item (e.g. 'AI' is contained in 'Artificial Intelligence').

    This ensures data quality regardless of LLM non-determinism.
    """
    # --- Pass 1: Remove category labels ---
    specific_skills = [s for s in result.required_technical_skills
                       if not _is_category_label(s)]
    if specific_skills:  # Only strip categories if at least one specific skill exists
        result.required_technical_skills = specific_skills

    # --- Pass 2: Deduplicate domains by substring containment ---
    domains = result.domain_experience
    deduplicated = []
    for domain in domains:
        # Keep this domain only if no other domain already subsumes it
        subsumed = any(
            other.lower() != domain.lower() and domain.lower() in other.lower()
            for other in domains
        )
        if not subsumed:
            deduplicated.append(domain)
    result.domain_experience = deduplicated

    return result

def _load_prompt(filename: str) -> str:
    """Read a prompt template file from the prompts/ directory."""
    path = _PROMPTS_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _apply_calibration(raw_score: int, mode: str, gap: GapAnalysis) -> int:
    """
    Deterministic score adjustment based on the calibration mode.

    Keeps score adjustment transparent and reproducible (Python-side, not LLM):
      - lenient:  +5 per transferable skill, -3 per missing skill.
      - standard: no adjustment — raw score is used as-is.
      - strict:   -10 per missing skill.

    Result is clamped to [0, 100].
    """
    n_missing = len(gap.missing_skills)
    n_transferable = len(gap.transferable_skills)

    if mode == "lenient":
        adjusted = raw_score + (n_transferable * 5) - (n_missing * 3)
    elif mode == "strict":
        adjusted = raw_score - (n_missing * 10)
    else:  # standard
        adjusted = raw_score

    return max(0, min(100, adjusted))


async def extract_jd_node(state: ScreenerState) -> dict:
    """
    Agent 1a — JD Extraction (async).
    Extracts structured requirements from the raw Job Description text.
    """
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(JDExtractionResult)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("extract_prompt.txt")),
        ("human", "Please extract the structured information from the following Job Description:\n\n{document_text}"),
    ])

    chain = prompt_template | structured_llm
    result: JDExtractionResult = await chain.ainvoke({
        "document_type": "Job Description",
        "document_text": state.jd_text,
    })

    # Post-processing: deterministic normalization (dedup + category label removal)
    result = _normalize_jd(result)

    return {"jd_skills": result}

async def extract_resume_node(state: ScreenerState) -> dict:
    """
    Agent 1b — Resume Extraction (async).
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
    result: ResumeExtractionResult = await chain.ainvoke({
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
    Applies deterministic score calibration then generates the human-readable
    hiring verdict, adjusted score, red flags, and interview areas.
    """
    if not state.gap_analysis:
        raise ValueError("Cannot generate recommendation: Gap analysis result is missing.")

    llm = get_llm(temperature=0.2)
    structured_llm = llm.with_structured_output(HiringRecommendation)

    ga = state.gap_analysis
    calibration_mode = state.calibration_mode

    # Deterministic score adjustment (Python-side, fully reproducible)
    calibrated_score = _apply_calibration(ga.match_score_raw, calibration_mode, ga)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", _load_prompt("recommend_prompt.txt")),
        ("human", "Generate the final hiring recommendation now."),
    ])

    chain = prompt_template | structured_llm
    result: HiringRecommendation = chain.invoke({
        "calibration_mode": calibration_mode,
        "calibrated_score": calibrated_score,
        "raw_score": ga.match_score_raw,
        "matching_skills": ", ".join(ga.matching_skills),
        "missing_skills": ", ".join(ga.missing_skills),
        "transferable_skills": ", ".join(ga.transferable_skills),
        "experience_gap": ga.experience_gap,
    })
    return {"final_recommendation": result}
