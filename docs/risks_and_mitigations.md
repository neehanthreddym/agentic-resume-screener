# Risks & Mitigations

## 1. Data Quality & Parsing Failures
**Risk:** Resumes often use complex two-column layouts, tables, or invisible text. Standard top-to-bottom text extraction (like naive PDF parsing) scrambles this text, mixing skills with experience and destroying the semantic meaning before the LLM even sees it.
**Mitigation:** I will use `PyMuPDF` (`fitz`) for block-level layout extraction rather than pure text streams. This preserves the logical reading order of two-column resumes. I will also implement a validation step to catch unreadable documents before passing them to the LangGraph pipeline.

## 2. LLM Hallucination & Output Parsing
**Risk:** The LLM might invent skills the candidate does not have ("hallucination") or return unstructured text that breaks the FastAPI backend when it expects a JSON object.
**Mitigation:**
- **Hallucination:** I will strictly prompt the Extraction Agent to quote directly from the source text.
- **Output Parsing:** I will use Pydantic models with LangChain's native `.with_structured_output()` to enforce a strict JSON schema. This ensures the output is always a valid object that can be safely processed by downstream nodes.

## 3. Algorithmic Bias
**Risk:** General-purpose LLMs have demonstrated significant bias, often penalizing candidates based on demographic proxies (like names or affiliations) or favoring specific formatting styles.
**Mitigation:** The system will NOT be used as a black-box decision maker (e.g., "Rank these candidates 1-10"). Instead, it acts as an *assistive extraction tool* that maps explicit resume claims to explicit JD requirements. The final decision remains with the human recruiter, armed with the extracted evidence.

## 4. Latency & Cost (Rate Limits)
**Risk:** Running three sequential LLM agents per resume could take 30+ seconds and hit API rate limits quickly, creating a poor user experience.
**Mitigation:** I am utilizing `llama-3.3-70b-versatile` via Groq, which offers extreme inference speeds (~500 tokens/sec). I have also configured `gemini-2.0-flash` via the Google GenAI SDK as a high-speed secondary provider to handle rate limits or outages. Additionally, extraction tasks are run in parallel to minimize overall execution time.
