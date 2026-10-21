"""Security helpers: PII redaction and rate-limit wiring.

Week 1 (Task 2): redact_pii masks emails and phone numbers.
Still TODO: street addresses, national IDs, and other identifiers.
HTTPS terminates at the reverse proxy / cloud load balancer, not in-app.
"""

import re

from slowapi import Limiter
from slowapi.util import get_remote_address

# Matches things like jane.doe+jobs@mail.example.com.au
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Finds *candidate* phone numbers: an optional "+", an optional "(", then digits
# mixed with spaces, dots, dashes, or parentheses. Examples it catches:
#   +61 412 345 678    (02) 9876 5432    555-123-4567    0412.345.678
# Candidates are filtered in _replace_phone, because this pattern alone would
# also match things like year ranges.
PHONE_CANDIDATE_PATTERN = re.compile(r"(?<!\w)\+?\(?\d[\d\s().-]{6,}\d(?!\w)")

# Resumes are full of date ranges like "2019 - 2023" (8 digits), which
# look like phone numbers. Anything matching this is left alone.
YEAR_RANGE_PATTERN = re.compile(r"^(19|20)\d{2}\s*[-–.]\s*(19|20)\d{2}$")

# Real phone numbers have 8–15 digits (15 is the international maximum).
# Fewer than 8 is usually a year, a salary, or a version number.
MIN_PHONE_DIGITS = 8
MAX_PHONE_DIGITS = 15


def _replace_phone(match: re.Match[str]) -> str:
    """Replace a candidate with [PHONE] only if it really looks like a phone number."""
    candidate = match.group(0)
    digit_count = sum(ch.isdigit() for ch in candidate)
    if not MIN_PHONE_DIGITS <= digit_count <= MAX_PHONE_DIGITS:
        return candidate
    if YEAR_RANGE_PATTERN.match(candidate.strip()):
        return candidate
    return "[PHONE]"


def redact_pii(text: str) -> str:
    """Return text with emails and phone numbers masked.

    Runs before anything is logged, saved to SQLite, or (later) sent to an LLM.
    Emails are redacted first, so digits inside an email address can't be
    mistaken for a phone number.
    """
    text = EMAIL_PATTERN.sub("[EMAIL]", text)
    text = PHONE_CANDIDATE_PATTERN.sub(_replace_phone, text)
    return text


limiter = Limiter(key_func=get_remote_address)
