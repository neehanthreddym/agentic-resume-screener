import pytest
from src.utils.experience import calculate_experience_years

class MockEntry:
    def __init__(self, duration, job_title="Engineer"):
        self.duration = duration
        self.job_title = job_title

def test_standard_range():
    # Jan 2023 to Jan 2024 is 13 months inclusive = 1.1
    experience = [MockEntry("Jan 2023 - Jan 2024")]
    assert calculate_experience_years(experience) == 1.1

def test_single_year_success():
    # 2023 is treated as Jan 1 2023 to Jan 1 2024 = 1.0 (12 months)
    experience = [MockEntry("2023")]
    assert calculate_experience_years(experience) == 1.0

def test_same_year_range_success():
    # 2023 - 2023 is treated as Jan 1 2023 to Jan 1 2024 = 1.0
    experience = [MockEntry("2023 - 2023")]
    assert calculate_experience_years(experience) == 1.0

def test_month_year_single_success():
    # Jun 2023 is Jun 1 to Jul 1 = 1 month (0.1)
    experience = [MockEntry("Jun 2023")]
    assert calculate_experience_years(experience) == 0.1

def test_combined_experience():
    # 2023 (1.0) + Jan 2024 - Jan 2025 (1.1) = 2.1 (25 months)
    experience = [
        MockEntry("2023"), # 12 mo
        MockEntry("Jan 2024 - Jan 2025") # 13 mo
    ]
    assert calculate_experience_years(experience) == 2.1
