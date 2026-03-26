"""
Deterministic experience year calculator.

Proven implementation from notebooks/02_structured_extraction.ipynb.

Key decision: We calculate total years from raw date strings (e.g., "Jun 2022 - Present")
instead of trusting the LLM's self-reported total_years_of_experience. The LLM anchors to
numbers it sees in the summary (e.g., "5+ years") which are self-reported and often inflated.
Deterministic math > LLM self-report for a structured, auditable output.

Return format: float encoded as {years}.{months}
  - 5 yrs 0 mo  → 5.0
  - 5 yrs 6 mo  → 5.6
  - 3 yrs 11 mo → 3.11
"""
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta


def _parse_date(s: str) -> datetime:
    """
    Parse a date string in common resume formats.

    Supports: "Jun 2022", "June 2022", "2022-06", "2022/06", "2022", "Present", "Now", "Current".
    """
    s = s.strip()
    if s.lower() in ("present", "now", "current"):
        return datetime.now()
    for fmt in ("%b %Y", "%B %Y", "%Y-%m", "%Y/%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Year-only fallback (e.g., "2020")
    if re.fullmatch(r"\d{4}", s):
        return datetime(int(s), 1, 1)
    raise ValueError(f"Unrecognized date format: {s!r}")


def calculate_experience_years(experience: list) -> float:
    """
    Calculate total professional experience from a list of ExperienceEntry objects.

    Sums the months across all roles, then formats as {years}.{remaining_months}.
    Overlapping roles are not deduplicated — consistent with how resumes present data.

    Args:
        experience: A list of ExperienceEntry Pydantic models, each with a `duration` field
                    formatted as "MMM YYYY - MMM YYYY" or "MMM YYYY - Present".

    Returns:
        Float encoded as years.months (e.g., 5.6 = 5 years, 6 months).
        Returns 0.0 if no parseable durations are found.
    """
    total_months = 0

    for entry in experience:
        if not entry.duration:
            continue

        # Normalize different dash characters
        raw = entry.duration.replace("–", "-").replace("—", "-")
        parts = re.split(r"\s*-\s*", raw, maxsplit=1)

        if len(parts) != 2:
            print(f"  [Experience] Skipping unparseable duration: {entry.duration!r}")
            continue

        try:
            start_dt = _parse_date(parts[0])
            end_dt = _parse_date(parts[1])
        except ValueError as e:
            print(f"  [Experience] {e} — skipping: {getattr(entry, 'job_title', '?')!r}")
            continue

        delta = relativedelta(end_dt, start_dt)
        role_months = delta.years * 12 + delta.months

        if role_months > 0:
            total_months += role_months

    years = total_months // 12
    rem_months = total_months % 12
    return float(f"{years}.{rem_months}")
