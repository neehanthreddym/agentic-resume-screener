# Evaluation Results & Failure Modes

This document tracks the performance of the AI Resume Screener pipeline, specifically focused on quality, hallucinations, and formatting issues identified during testing.

## Smoke Test Observations (March 26, 2026)

### 1. Skill Classification Blur (⚠️)
- **Reference**: Detailed test run available in `notebooks/03_pipeline_testing`.ipynb.
- **Issue**: The `extract_jd` node incorrectly categorized "system design" and "reliability" as `soft_skills`. 
- **Example Output**:
  ```json
  ...
  "domain_experience": [
      "AI",
      "Artificial Intelligence"
    ],
    "soft_skills": [
      "system design",
      "reliability",
      "operational excellence",
      "communication",
      "collaboration"
    ]
  ...
  ```
- **Analysis**: In a software engineering context, these are hard technical competencies. The LLM's classification logic tends to blur the line between "process-oriented technical skills" and "pure interpersonal soft skills."
- **Impact**: Soft skills and hard skills are analyzed separately in the gap analysis. This blur can lead to missing technical gaps if a required hard skill is "buried" in the soft skills list.

### 2. Gap Analysis JSON Formatting (Fixed)
- **Issue**: LLM attempted to include explanatory text ("Skill X for Y") within the `transferable_skills` list, breaking JSON parsing.
- **Example Failure**:
  ```json
  "transferable_skills": [
    "FastAPI" for "APIs"
  ]
  ```
- **Resolution**: Prompt updated to enforce `"CandidateSkill (maps to Requirement)"` string format.