from typing import Any, Optional

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    resume_text: str
    job_description_text: str
    user_id: Optional[str] = None


class SafetyFlag(BaseModel):
    flag_type: str
    score: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TelemetryMetadata(BaseModel):
    request_id: str
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None
    chunk_ids: list[str] = Field(default_factory=list)
    latency_ms: Optional[int] = None
    token_estimate: Optional[int] = None
    safety_flags: list[str] = Field(default_factory=list)
    error_code: Optional[str] = None


class CompareResponse(BaseModel):
    gap_analysis: Optional[str] = None
    recommended_roles: list[str] = Field(default_factory=list)
    learning_paths: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    telemetry: TelemetryMetadata
