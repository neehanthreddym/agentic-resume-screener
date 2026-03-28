# Evaluation Results & Failure Modes

This document tracks the performance of the AI Resume Screener pipeline, specifically focused on quality, hallucinations, and formatting issues identified during testing.

## Pipeline Optimization Outcomes (March 27, 2026)

The following issues were identified and resolved during the transition from prototype to production-grade pipeline.

### 1. Extraction Scope Inflation (Fixed)
- **Issue**: The `extract_jd` node was extracting hard skills from responsibility sentences (e.g., "Implement APIs" yielded both a responsibility and a required skill "APIs").
- **Resolution**: Updated `extract_prompt.txt` with a strict "Extraction Scope" rule: skills MUST only be extracted from explicit requirements sections. Responsibilities are now treated as context for the `core_responsibilities` field only.

### 2. Academic Skill Noise (Fixed)
- **Issue**: Candidate resumes often list course names (e.g., "Operating Systems", "Algorithms") which the LLM extracted as professional skills, falsely inflating the match score.
- **Resolution**: Enforced an "Active Competency" rule in the extraction prompt. Skills must be tools, languages, or frameworks used in a project or role, not just academic coursework headers.

### 3. Domain Context Pollution (Fixed)
- **Issue**: Industry domains (e.g., "Artificial Intelligence", "FinTech") often appeared in `missing_skills` or `matching_skills` despite being higher-level background context.
- **Resolution**: Separated `domain_experience` into a distinct context field in `GapAnalysis`. The `analyze_prompt.txt` now explicitly forbids domain names from entering the hard skills comparison list.

### 4. Transferable Skill Type Mismatch (Fixed)
- **Issue**: The LLM occasionally mapped different "types" of skills (e.g., "FastAPI" framework mapping to "Go" language), which is technically inaccurate for senior roles.
- **Resolution**: Updated few-shot examples in `analyze_prompt.txt` to enforce same-category mapping (e.g., Framework → Framework, Tool → Tool). Added `calibration_mode` to allow for stricter or more lenient mapping logic.

### 5. Pipeline Latency (Optimized)
- **Baseline**: Sequential execution in LangGraph (JD → Resume → Analysis) resulted in ~1m 3s total latency on Gemini.
- **Optimization**: Redesigned graph topology for concurrent extraction. Using `async def` and `ainvoke()`, the `extract_jd` and `extract_resume` nodes now run in parallel.
- **Result**: Reduced end-to-end latency by ~30–40%, bringing the target under 40s.

## Legacy Issues (Resolved)

### 6. Experience Calculation Failure (Fixed)
- **Issue**: Single-year durations (e.g., "2023") or same-year ranges were skipped by the parser.
- **Resolution**: Updated `src/utils/experience.py` to handle single dates and treat year-only entries as 12-month periods. Verified with unit tests.