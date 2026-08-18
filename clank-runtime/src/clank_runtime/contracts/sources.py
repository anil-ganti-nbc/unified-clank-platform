"""Source, evidence, and multi-dimensional coverage contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceRole(StrEnum):
    PRIMARY_OFFICIAL = "primary_official"
    REGIONAL_OFFICIAL = "regional_official"
    SPECIALIST_EDITORIAL = "specialist_editorial"
    SUPPORT_INFRASTRUCTURE = "support_infrastructure"
    CERTIFICATION = "certification"
    RETAILER = "retailer"
    DISTRIBUTOR = "distributor"
    AGGREGATOR = "aggregator"
    OTHER = "other"


class SourceCapability(StrEnum):
    AUTHORITATIVE_IDENTITY = "authoritative_identity"
    AUTHORITATIVE_SPECS = "authoritative_specs"
    AUTHORITATIVE_AVAILABILITY = "authoritative_availability"
    EARLY_SIGNAL = "early_signal"
    LEAK_SIGNAL = "leak_signal"
    REGIONAL_SIGNAL = "regional_signal"
    PRICE_SIGNAL = "price_signal"
    FIRMWARE_SIGNAL = "firmware_signal"
    CERTIFICATION_SIGNAL = "certification_signal"
    EDITORIAL_CONTEXT = "editorial_context"


class EvidenceKind(StrEnum):
    LEAK = "leak"
    RUMOUR = "rumour"
    EARLY_SIGNAL = "early_signal"
    NEEDS_VERIFICATION = "needs_verification"
    PRE_RELEASE_EVIDENCE = "pre_release_evidence"
    AUTHORITATIVE_STATE = "authoritative_state"


class SourceDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    role: SourceRole
    region: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    capabilities: frozenset[SourceCapability] = frozenset()
    authority_level: str = Field(min_length=1)
    delivery_permissions: frozenset[str] = frozenset()
    lifecycle_state: str = Field(min_length=1)
    known_limitations: tuple[str, ...] = ()


class CoverageFact(BaseModel):
    """A coverage claim; role, region, and surface are never flattened."""

    model_config = ConfigDict(extra="forbid")

    domain: str = Field(min_length=1)
    entity: str = Field(min_length=1)
    region: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    source_role: SourceRole
    source_id: str = Field(min_length=1)
    operationally_healthy: bool
    intelligence_coverage_sufficient: bool | None = None


class EvidenceClaim(BaseModel):
    """Provenance-preserving claim; specialist evidence is not authoritative by role."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_role: SourceRole
    kind: EvidenceKind
    subject_id: str = Field(min_length=1)
    claim: dict[str, Any] = Field(default_factory=dict)
    authoritative_state_update_allowed: bool = False
    independently_verified: bool = False

    def can_update_authoritative_state(self) -> bool:
        return self.authoritative_state_update_allowed and self.independently_verified

