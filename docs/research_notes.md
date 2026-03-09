# Research Notes — Phase 2
# AI-Powered Resume Screener

## Key Takeaways

### 1. PDF Parsing: Two-Column Layouts Are a Real Failure Mode
- At least 15% of real-world resumes use multi-column layouts; naive top-to-bottom text extraction scrambles section boundaries and mixes skills with work experience.
- **Design decision:** Use `pdfplumber` (coordinate-aware extraction) over PyPDF2. Add a plain-text preview step in the Streamlit UI so users can visually verify what was extracted before analysis runs. If layout detection is uncertain, fall back to single-column reading order rather than returning broken text.

### 2. Structured JSON Extraction: Instructor + Pydantic + Retry Loop
- The industry-standard pattern is: define a Pydantic schema → wrap LLM client with `instructor` → catch validation errors → auto-retry with error context fed back to the model (up to a max retry limit).
- A secondary "JSON fixer" prompt (asking the LLM to repair its own invalid output using the schema + error message) dramatically improves parse success rate.
- **Design decision:** All three LangGraph agents will return typed Pydantic objects, never raw strings. Validation failures are logged as errors, not silently swallowed.

### 3. LLM Bias in Hiring Is a Known, Documented Risk
- Empirical studies show LLMs prefer male-coded and white-associated names on otherwise identical resumes. Style and fluency also create unfair proxies.
- **Design decision:** Frame all outputs as *advisory recommendations*, not decisions. The UI copy and README will clearly state: "This tool supports human reviewers — it does not make hiring decisions." Focus recommendation rationale strictly on skills and evidence from the text, not overall writing quality or name signals.
