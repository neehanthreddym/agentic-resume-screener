# Project Progress Tracker
# AI-Powered Resume Screener

## Phase 1 — Ideation & Problem Definition
- [x] Problem statement written
- [x] Target user and use case defined
- [x] AI approach chosen (Structured Agentic Pipeline — LangGraph, NOT RAG)
- [x] Success metrics defined (quality + cost + latency)
- [x] MVP scope confirmed and stretch goals separated

## Phase 2 — Research & Feasibility
- [x] Related projects and papers reviewed
- [x] Data/knowledge source confirmed (JD as PDF/TXT, Resume as PDF/DOCX — no external KB needed)
- [x] LLM and embedding model chosen with justification
- [x] Key risks documented (hallucination, cost, latency, data quality)

## Phase 3 — System Design & Architecture
- [x] Architecture diagram created (assets/architecture)
- [x] Folder structure initialized and pushed to GitHub
- [x] Tool stack finalized with written justifications

## Phase 4 — Data & Knowledge Base Preparation
- [x] Sample JD + resume pairs collected (15 pairs for MVP eval)
- [ ] Document parsing tested — pdfplumber (PDF), python-docx (DOCX), open() (TXT)
- [ ] Evaluation dataset created (20 JD/resume pairs with human-labeled verdicts)
- [ ] Structured extraction tested on sample inputs

## Phase 5 — Prompt Engineering & Chain Design
- [ ] System prompts v1 written for all three LLM agents (extract, analyze, recommend)
- [ ] Prompt versions tracked (Google Sheets or LangSmith)
- [ ] LangGraph pipeline built end-to-end
- [ ] Structured Pydantic output schema defined and validated
- [ ] Guardrails added (off-topic input rejection, parse failure fallback)

## Phase 6 — Evaluation & Quality Assurance
- [ ] Manual eval set of 20 JD/resume pairs run through pipeline
- [ ] LLM-as-judge scoring implemented (faithfulness + recommendation accuracy)
- [ ] Structured output parse success rate measured (target: 100%)
- [ ] Latency benchmarked (target: < 15s end-to-end)
- [ ] Cost per analysis calculated (target: < $0.05)
- [ ] Failure modes documented in evaluation/results.md

## Phase 7 — Production Code & Engineering Quality
- [ ] Code refactored into clean modules under src/
- [ ] Type hints and docstrings added throughout
- [ ] ruff + black + mypy passing
- [ ] pre-commit hooks configured
- [ ] Unit tests written and passing (pytest)
- [ ] All configs externalized to configs/config.yaml
- [ ] Structured logging with loguru

## Phase 8 — API & Application Layer
- [ ] FastAPI app built with /analyze, /health, /info endpoints
- [ ] Pydantic request/response schemas defined
- [ ] Streaming response considered (or polling for long jobs)
- [ ] Streamlit UI built with upload interface + formatted results display
- [ ] Source traceability shown in UI (which text drove each recommendation)

## Phase 9 — Containerization & Deployment
- [ ] Dockerfile written and tested locally
- [ ] .dockerignore configured
- [ ] GitHub Actions CI/CD pipeline (lint → test → build)
- [ ] App deployed to Hugging Face Spaces (Streamlit) or Render (FastAPI)
- [ ] Live public URL confirmed and added to README

## Phase 10 — Monitoring & Observability
- [ ] LLM call logging active (query, response, tokens, latency, cost)
- [ ] Cost tracking documented per-analysis
- [ ] Parse failure logging in place
- [ ] Monitoring plan documented in ARCHITECTURE.md

## Phase 11 — Documentation & Portfolio Presentation
- [ ] README.md completed (demo GIF, architecture diagram, eval results, usage)
- [ ] ARCHITECTURE.md written (design decisions, tradeoffs, data flow)
- [ ] Blog post or demo video published (dev.to / Loom)
- [ ] Interview talking points prepared (6 questions)

## Phase 12 — Review & Retrospective
- [ ] Final senior engineer checklist reviewed
- [ ] Project shared on GitHub, LinkedIn, and portfolio
- [ ] Stretch goals identified for next iteration
- [ ] Next project or skill gap identified
