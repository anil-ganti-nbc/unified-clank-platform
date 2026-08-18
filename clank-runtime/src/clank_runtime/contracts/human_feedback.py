"""Shared human-QC and review-queue contracts.

This module defines the portable review semantics only. It does not provide a
database, queue worker, UI toolkit, or domain truth model. Individual Clanks
own the surrounding fields and may advertise partial or unsupported support.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OperatorDisposition(StrEnum):
    """The four shared human-QC labels."""

    USEFUL = "USEFUL"
    NOT_USEFUL = "NOT USEFUL"
    FALSE_POSITIVE = "FALSE POSITIVE"
    OUT_OF_STOCK = "OUT OF STOCK"


class ReviewState(StrEnum):
    """Queue state; intentionally separate from an operator disposition."""

    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    DEFERRED = "DEFERRED"
    DISMISSED = "DISMISSED"


class FindingReference(BaseModel):
    """Stable identity for feedback; never use row position as identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clank_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    event_id: str | None = None
    lead_id: str | None = None
    run_id: str | None = None


class FeedbackProvenance(BaseModel):
    """Who, when, and through which traceable path supplied feedback."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor: str = Field(min_length=1)
    recorded_at: datetime
    channel: str = Field(min_length=1, description="For example: web_qc, desktop_qc, or api")
    source_reference: str | None = None
    build_sha: str | None = None
    database_id: str | None = None
    run_id: str | None = None
    epoch_id: str | None = None


class ReviewItem(BaseModel):
    """A queue item whose underlying finding remains owned by its Clank."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: FindingReference
    review_state: ReviewState = ReviewState.UNREVIEWED
    disposition: OperatorDisposition | None = None

    @model_validator(mode="after")
    def validate_disposition_state(self) -> ReviewItem:
        if self.disposition is not None and self.review_state is ReviewState.UNREVIEWED:
            raise ValueError("a disposition requires a non-UNREVIEWED review state")
        return self


class FeedbackRecord(BaseModel):
    """Append-only human feedback; later records may supersede earlier ones."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    finding: FindingReference
    disposition: OperatorDisposition
    review_state: ReviewState = ReviewState.REVIEWED
    provenance: FeedbackProvenance
    supersedes_feedback_id: str | None = None
    operator_note: str | None = None

    @model_validator(mode="after")
    def feedback_is_reviewed(self) -> FeedbackRecord:
        if self.review_state is not ReviewState.REVIEWED:
            raise ValueError("a disposition record must have REVIEWED state")
        return self


class ModelPrediction(BaseModel):
    """Optional machine output; never a substitute for operator disposition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(min_length=1)
    predicted_label: str = Field(min_length=1)
    probability: float | None = Field(default=None, ge=0, le=1)
    generated_at: datetime


class ReviewProgress(BaseModel):
    """Measured queue progress; None means the Clank cannot measure it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    total: int | None = Field(default=None, ge=0)
    reviewed: int | None = Field(default=None, ge=0)
    unreviewed: int | None = Field(default=None, ge=0)
    useful: int | None = Field(default=None, ge=0)
    not_useful: int | None = Field(default=None, ge=0)
    false_positive: int | None = Field(default=None, ge=0)
    out_of_stock: int | None = Field(default=None, ge=0)

    @classmethod
    def from_items(cls, items: Sequence[ReviewItem]) -> ReviewProgress:
        counts = {d: 0 for d in OperatorDisposition}
        reviewed = 0
        for item in items:
            if item.review_state is ReviewState.REVIEWED:
                reviewed += 1
            if item.disposition is not None:
                counts[item.disposition] += 1
        return cls(
            total=len(items),
            reviewed=reviewed,
            unreviewed=sum(item.review_state is ReviewState.UNREVIEWED for item in items),
            useful=counts[OperatorDisposition.USEFUL],
            not_useful=counts[OperatorDisposition.NOT_USEFUL],
            false_positive=counts[OperatorDisposition.FALSE_POSITIVE],
            out_of_stock=counts[OperatorDisposition.OUT_OF_STOCK],
        )


class HumanQCCapability(StrEnum):
    HUMAN_QC_FEEDBACK = "HUMAN_QC_FEEDBACK"


class CapabilitySupport(StrEnum):
    SUPPORTED_NATIVE = "SUPPORTED_NATIVE"
    SUPPORTED_ADAPTER = "SUPPORTED_ADAPTER"
    PARTIAL = "PARTIAL"
    PLANNED = "PLANNED"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class HumanQCCapabilityDeclaration(BaseModel):
    """Dynamic capability advertisement without requiring every legacy Clank to support it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    capability: HumanQCCapability = HumanQCCapability.HUMAN_QC_FEEDBACK
    support: CapabilitySupport = CapabilitySupport.UNKNOWN
    note: str | None = None


class HumanFeedbackStore(Protocol):
    """Persistence boundary; implementations must append, not overwrite history."""

    def append(self, record: FeedbackRecord) -> None:
        ...

    def history(self, finding: FindingReference) -> Sequence[FeedbackRecord]:
        ...


def apply_disposition(
    item: ReviewItem,
    disposition: OperatorDisposition,
    provenance: FeedbackProvenance,
    *,
    supersedes_feedback_id: str | None = None,
    operator_note: str | None = None,
) -> tuple[ReviewItem, FeedbackRecord]:
    """Return the reviewed queue item and append-only record to persist.

    This pure helper does not delete the underlying finding or write storage.
    """

    record = FeedbackRecord(
        finding=item.reference,
        disposition=disposition,
        provenance=provenance,
        supersedes_feedback_id=supersedes_feedback_id,
        operator_note=operator_note,
    )
    reviewed = item.model_copy(
        update={"review_state": ReviewState.REVIEWED, "disposition": disposition}
    )
    return reviewed, record


def next_unreviewed(
    items: Sequence[ReviewItem], *, after: FindingReference | None = None
) -> ReviewItem | None:
    """Select the next eligible item, wrapping once, without relying on row number."""

    if not items:
        return None
    start = 0
    if after is not None:
        for index, item in enumerate(items):
            if item.reference == after:
                start = index + 1
                break
    ordered = (*items[start:], *items[:start])
    return next((item for item in ordered if item.review_state is ReviewState.UNREVIEWED), None)
