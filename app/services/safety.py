"""Safety & evaluation stub.

Every LLM response should be checked for hallucinations, unsafe advice,
privacy leaks, prompt injection, toxicity, and bias.
"""

from typing import Any

from app.schemas.compare import SafetyFlag


def evaluate(text: str, *, context: dict[str, Any] | None = None) -> list[SafetyFlag]:
    """Return safety flags and scores. Currently empty on purpose."""
    return []
