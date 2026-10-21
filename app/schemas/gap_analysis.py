"""Request/response shapes for POST /gap-analysis.

Week 1: the response is a placeholder. Once RAG + the LLM are wired in
(Task 6 onward), the orchestrator fills these fields with real output.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GapAnalysisRequest(BaseModel):
    """What the client sends: raw resume + job description text."""

    resume_text: str = Field(min_length=1)
    job_description_text: str = Field(min_length=1)
    # Used for the per-user daily quota (Task 3). Missing = "anonymous".
    user_id: Optional[str] = None


class GapAnalysisResponse(BaseModel):
    """What the API returns. Every field except request_id is placeholder data for now."""

    # Same id that will appear in logs, telemetry, and the interactions table,
    # so one request can be traced end to end.
    request_id: str
    # "placeholder" tells clients the analysis isn't real yet.
    status: Literal["placeholder", "success"] = "placeholder"
    gap_analysis: str
    missing_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
