"""Security stubs: PII redaction and rate-limit wiring.

Replace identity redaction with real detectors before any LLM call.
HTTPS terminates at the reverse proxy / cloud load balancer, not in-app.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


def redact_pii(text: str) -> str:
    """Return text with PII removed before LLM / persistence.

    Implement: emails, phone numbers, street addresses, national IDs,
    and other identifiers. Currently a no-op so you can wire the pipeline.
    """
    return text


limiter = Limiter(key_func=get_remote_address)
