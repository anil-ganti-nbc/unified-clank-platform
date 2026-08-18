"""Composable contracts for the Unified Clank constitutional invariants."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EpistemicStatus(StrEnum):
    UNKNOWN = "unknown"
    UNRESOLVED = "unresolved"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED = "unsupported"
    NEEDS_VERIFICATION = "needs_verification"
    CONFIRMED = "confirmed"


class ObservationHealth(StrEnum):
    HEALTHY = "healthy"
    PARTIAL = "partial"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class PipelineStage(StrEnum):
    OBSERVE = "observe"
    FETCH = "fetch"
    PARSE = "parse"
    EXTRACT = "extract"
    NORMALISE = "normalise"
    IDENTIFY = "identify"
    INTERPRET = "interpret"
    CLASSIFY = "classify"
    SCORE_FILTER = "score_filter"
    EVENT = "event"
    DELIVERY = "delivery"


class DeliveryState(StrEnum):
    EVENT_CREATED = "event_created"
    EVENT_ELIGIBLE = "event_eligible"
    DELIVERY_QUEUED = "delivery_queued"
    DELIVERY_ATTEMPTED = "delivery_attempted"
    DELIVERY_SUCCEEDED = "delivery_succeeded"
    DELIVERY_FAILED = "delivery_failed"
    DELIVERY_RETRIED = "delivery_retried"
    DELIVERY_SUPPRESSED = "delivery_suppressed"


class ClaimState(StrEnum):
    REPORTED = "reported"
    CORROBORATED = "corroborated"
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    SUPERSEDED = "superseded"


class ExecutionProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str | None = None
    launcher: str | None = None
    scheduler: str | None = None
    process_identity: str | None = None
    build_sha: str | None = None
    image_id: str | None = None
    database_id: str | None = None
    run_id: str | None = None
    epoch_id: str | None = None


class ObservationResult(BaseModel):
    """An absence is authoritative only when the relevant observation is healthy."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    observed_at: datetime
    health: ObservationHealth
    result_count: int | None = Field(default=None, ge=0)
    absence_authority: bool = False
    removal_authority: bool = False
    execution: ExecutionProvenance | None = None

    def can_advance_absence(self) -> bool:
        return self.health is ObservationHealth.HEALTHY and self.result_count == 0


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: PipelineStage
    succeeded: bool | None = None
    status: EpistemicStatus = EpistemicStatus.UNKNOWN
    reason: str | None = None
    observed_at: datetime | None = None


class DeliveryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    state: DeliveryState
    attempted_at: datetime | None = None
    delivery_id: str | None = None
    reason: str | None = None


class RawEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    captured_at: datetime
    content_hash: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    immutable: bool = True


class Interpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpretation_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    derived_at: datetime
    status: EpistemicStatus = EpistemicStatus.UNKNOWN
    conclusion: dict[str, Any] = Field(default_factory=dict)
    supersedes_interpretation_id: str | None = None


class AgentClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    claimant: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    state: ClaimState = ClaimState.REPORTED
    evidence_references: tuple[str, ...] = ()
