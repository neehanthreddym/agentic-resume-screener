# Project Brief — AI-Powered Resume Screener

## Problem Statement

Recruiters spend an average of 6–7 seconds reviewing a resume, and most ATS systems rely on brittle keyword matching that misses strong candidates with transferable skills. There is a gap between *what a resume says* and *what a skilled recruiter infers* — and that inference requires genuine language understanding, not pattern matching.

## One-Paragraph Brief

This project is an **agentic LLM pipeline** that reasons about candidate–job fit the way a senior recruiter actually thinks. Given a job description and a resume (PDF, DOCX, or plain text), the system extracts structured skills and requirements from each document, performs a semantic gap analysis that accounts for transferable skills, and produces a calibrated, evidence-backed hiring recommendation in plain English. The output includes a match score (0–100), a skill gap table distinguishing present vs. missing vs. inferred-transferable skills, a top-3 list of interview focus areas, and a flags section for vague or contradictory claims. The system is built as a three-agent LangGraph pipeline with Pydantic-enforced structured output served over FastAPI, with a Streamlit UI for interactive demos. The target users are HR teams and hiring managers at SMBs who lack enterprise ATS tooling.

## Target Users

| User | Pain Point |
|------|-----------|
| HR Managers / Recruiters | Manually reviewing 50–200 resumes per role is time-consuming and inconsistent |
| Hiring Managers | Need a second opinion that surfaces the *right* questions to ask, not just a score |
| Job Seekers *(stretch)* | Want to self-assess before applying and understand specific gaps |

## Why LLM/AI is the Right Tool

This is a **structured reasoning problem**, not a retrieval or classification problem. The system must:
- Understand vague or implicit skill descriptions ("experience with large-scale data pipelines" → infer distributed systems familiarity)
- Infer transferable skills across adjacent technologies
- Produce grounded, evidence-linked rationale — not a black-box score

Pure NLP/ML (TF-IDF cosine similarity, classification models) cannot do this reliably. An LLM reasoning pipeline with structured output can.

## AI Approach

**Structured Agentic Pipeline** using LangGraph (not RAG — no external knowledge base needed for single-document analysis).

```
Resume (PDF / DOCX / TXT) + JD (PDF / TXT)
       ↓
  [Parse & Clean]         — pdfplumber (PDF) | python-docx (DOCX) | open() (TXT)
       ↓
  [Extraction Agent]      — LLM Call #1: extract structured skills/requirements from each doc
       ↓
  [Gap Analysis Agent]    — LLM Call #2: compare, score, identify gaps & transferable skills
       ↓
  [Recommendation Agent]  — LLM Call #3: generate hiring recommendation + interview questions
       ↓
  Pydantic Structured Output → FastAPI → Streamlit UI
```

## Technology Decisions

| Component | Choice | Justification |
|-----------|--------|---------------|
| LLM | `llama-3.3-70b-versatile` via Groq | Free tier, ~500 tok/s, strong reasoning |
| Fallback LLM | `gpt-4o-mini` (OpenAI) | If Groq rate limits hit |
| Structured output | `instructor` + Pydantic | Forces valid JSON schema — 100% parse success target |
| Orchestration | LangGraph | Multi-step stateful pipeline; matches target role skillset |
| PDF parsing | `pdfplumber` | Best plain-text extraction for PDF resumes and job descriptions |
| DOCX parsing | `python-docx` | Standard library for Word document extraction; most resumes are submitted as .docx |
| API layer | FastAPI | Async, typed, auto-documented |
| UI | Streamlit | Fastest path to a demo-able, portfolio-visible product |
| Deployment | Hugging Face Spaces | Free, public, indexed by recruiters |

## Success Metrics

| Dimension | Target | Measurement Method |
|-----------|--------|--------------------|
| Recommendation accuracy | ≥ 80% agreement with human reviewer | Manual eval set of 20 JD/resume pairs |
| Faithfulness | Every claim traceable to source text | LLM-as-judge scoring |
| Latency | < 15 seconds end-to-end | Timed on 10 test cases |
| Cost per analysis | < $0.05 | Token count × Groq/OpenAI pricing |
| Structured output parse rate | 100% | Unit tests on Pydantic schema validation |

## MVP Scope

- Resume upload: PDF, DOCX, and plain text supported
- JD upload: PDF and plain text supported
- Three-agent LangGraph pipeline with Pydantic output
- Match score + skill gap table + hiring recommendation + interview focus areas + red flags
- FastAPI `/analyze` and `/health` endpoints
- Streamlit UI with upload + formatted results
- Dockerized + deployed to Hugging Face Spaces

## Stretch Goals

- Batch mode: analyze N resumes against one JD and rank candidates
- Candidate-facing mode: "How do I improve this resume for this job?"
- RAG layer: pull in industry role benchmarks or salary data
- LangSmith tracing on all three agent calls
- Comparison view: side-by-side candidate ranking dashboard
