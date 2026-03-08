# AI-Powered Resume Screener

> An agentic LLM pipeline that reasons about candidate–job fit the way a senior recruiter thinks — not keyword matching, but semantic role alignment, transferable skill inference, and evidence-backed hiring recommendations.

<!-- Badges — update as project progresses -->
![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)
![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange?style=for-the-badge)
![LLM](https://img.shields.io/badge/LLM-Llama%203.3%2070B%20%7C%20GPT--4o--mini-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

---

## Problem

Recruiters spend an average of 6–7 seconds on a resume. ATS systems miss strong candidates with transferable skills because they rely on brittle keyword matching. There is a gap between *what a resume says* and *what a skilled recruiter infers* — and that inference requires language understanding, not pattern matching.

## What This Does

Upload a **job description** (PDF or text) and a **resume** (PDF, DOCX, or text). Get back:

| Output | Description |
|--------|-------------|
| **Match Score** | 0–100 calibrated fit score |
| **Skill Gap Analysis** | Present vs. required vs. transferable skills |
| **Hiring Recommendation** | Hire / Strong Hire / Hold / Reject with plain-English rationale |
| **Interview Focus Areas** | Top 3 questions to probe based on gaps |
| **Red Flags** | Vague claims, contradictions, or missing evidence |

## Architecture

> Architecture diagram will be added in Phase 3.

```
Resume (PDF / DOCX / TXT) + JD (PDF / TXT)
       ↓
  [Parse & Clean]         — pdfplumber (PDF) | python-docx (DOCX) | open() (TXT)
       ↓
  [Extraction Agent]      — LLM #1: structured skill/requirement extraction
       ↓
  [Gap Analysis Agent]    — LLM #2: semantic comparison + scoring
       ↓
  [Recommendation Agent]  — LLM #3: hiring recommendation + interview questions
       ↓
  Pydantic Output → FastAPI → Streamlit UI
```

## Tech Stack

| Component | Tool |
|-----------|------|
| Orchestration | LangGraph |
| LLM (Primary) | `llama-3.3-70b-versatile` via Groq |
| LLM (Fallback) | `gpt-4o-mini` via OpenAI |
| Structured Output | `instructor` + Pydantic |
| PDF Parsing | `pdfplumber` |
| DOCX Parsing | `python-docx` |
| API | FastAPI |
| UI | Streamlit |
| Deployment | Hugging Face Spaces |

## Getting Started

> Setup instructions will be added in Phase 7.

```bash
git clone https://github.com/yourusername/agentic-resume-screener.git
cd agentic-resume-screener
cp .env.example .env
# Fill in your API keys in .env
pip install -r requirements.txt
```

## Evaluation Results

> Evaluation results will be added in Phase 6.

## Live Demo

> Live demo link will be added after deployment.

## License

MIT
