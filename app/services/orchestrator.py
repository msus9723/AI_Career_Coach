"""Agent orchestration stub.

Fill in: tool routing, RAG retrieval, LLM compare, learning paths,
interview questions, and reasoning. This layer should call services.rag,
services.tools, then services.safety before returning.
"""

from app.schemas.compare import CompareRequest, CompareResponse, TelemetryMetadata


def compare(payload: CompareRequest, request_id: str) -> CompareResponse:
    """Return gap analysis, roles, learning paths, questions, and safety flags."""
    _ = (payload, request_id, CompareResponse, TelemetryMetadata)
    raise NotImplementedError(
        "Wire RAG, LLM compare, tools, and safety in app.services.orchestrator.compare"
    )
