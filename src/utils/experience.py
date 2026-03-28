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


def _parse_date(s: str, is_end: bool = False) -> datetime:
    """
    Parse a date string in common resume formats.

    Supports: "Jun 2022", "June 2022", "2022-06", "2022/06", "2022", "Present", "Now", "Current".
    
    If is_end is True, we return the logical end of the period (e.g., "2022" -> "2023-01-01")
    to ensure durations are inclusive.
    """
    s = s.strip()
    if s.lower() in ("present", "now", "current"):
        return datetime.now()
    
    # Check Year-only first for is_end logic
    if re.fullmatch(r"\d{4}", s):
        year = int(s)
        return datetime(year + 1, 1, 1) if is_end else datetime(year, 1, 1)

    for fmt in ("%b %Y", "%B %Y", "%Y-%m", "%Y/%m"):
        try:
            dt = datetime.strptime(s, fmt)
            if is_end:
                # Move to the first day of the NEXT month
                return dt + relativedelta(months=1)
            return dt
        except ValueError:
            continue
    
    raise ValueError(f"Unrecognized date format: {s!r}")


def calculate_experience_years(experience: list) -> float:
    """
    Calculate total professional experience from a list of ExperienceEntry objects.

    Sums the months across all roles, then formats as {years}.{remaining_months}.
    Overlapping roles are not deduplicated — consistent with how resumes present data.

    Args:
        experience: A list of ExperienceEntry Pydantic models, each with a `duration` field
                    formatted as "MMM YYYY - MMM YYYY", "MMM YYYY - Present", or "YYYY".

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

        try:
            if len(parts) == 2:
                start_dt = _parse_date(parts[0], is_end=False)
                end_dt = _parse_date(parts[1], is_end=True)
            else:
                # Single date case (e.g. "2023" or "Jun 2023")
                start_dt = _parse_date(parts[0], is_end=False)
                end_dt = _parse_date(parts[0], is_end=True)
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
