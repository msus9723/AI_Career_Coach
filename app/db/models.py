from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resume_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    jd_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    response_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    redacted_resume_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    redacted_jd_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    safety_flags: Mapped[list["SafetyFlag"]] = relationship(back_populates="interaction")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="interaction")


class SafetyFlag(Base):
    __tablename__ = "safety_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), index=True)
    flag_type: Mapped[str] = mapped_column(String(64))
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    interaction: Mapped["Interaction"] = relationship(back_populates="safety_flags")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), index=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_ids_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    interaction: Mapped["Interaction"] = relationship(back_populates="metrics")
