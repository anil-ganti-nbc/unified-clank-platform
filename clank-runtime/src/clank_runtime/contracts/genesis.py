"""Production Genesis contracts.

These contracts describe the authority boundary between exploratory development
and the first authoritative production epoch. They intentionally contain no
storage, deployment, or intelligence implementation.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatastoreRole(StrEnum):
    DEVELOPMENT_CORPUS = "development_corpus"
    SOAK = "soak"
    PRODUCTION = "production"
    HISTORICAL_ARCHIVE = "historical_archive"
    TEST = "test"
    REPLAY = "replay"


class GenesisCapability(StrEnum):
    SUPPORTED_NATIVE = "supported_native"
    SUPPORTED_ADAPTER = "supported_adapter"
    PARTIAL = "partial"
    PLANNED = "planned"
    NOT_APPLICABLE = "not_applicable"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class GenesisGate(StrEnum):
    DEVELOPMENT_SOAK_COMPLETE = "development_soak_complete"
    SOURCE_SET_FROZEN = "source_set_frozen"
    SERIOUS_IDENTITY_ERRORS_RESOLVED = "serious_identity_errors_resolved"
    CLASSIFICATION_REVIEW_COMPLETE = "classification_review_complete"
    NORMALISATION_REVIEW_COMPLETE = "normalisation_review_complete"
    SOURCE_HEALTH_VALIDATED = "source_health_validated"
    UNEXPECTED_ZERO_BEHAVIOUR_VALIDATED = "unexpected_zero_behaviour_validated"
    PARTIAL_FAILURE_BEHAVIOUR_VALIDATED = "partial_failure_behaviour_validated"
    DUPLICATE_BEHAVIOUR_VALIDATED = "duplicate_behaviour_validated"
    REMOVAL_BEHAVIOUR_VALIDATED = "removal_behaviour_validated"
    BASELINE_FIREWALL_VALIDATED = "baseline_firewall_validated"
    DEVELOPMENT_ARCHIVE_VERIFIED = "development_archive_verified"
    FRESH_PRODUCTION_DB_CREATED = "fresh_production_db_created"
    PRODUCTION_BASELINE_COMPLETE = "production_baseline_complete"
    NO_BASELINE_ALERT_AVALANCHE = "no_baseline_alert_avalanche"
    DELIVERY_DEDUPE_HISTORY_ACCOUNTED_FOR = "delivery_dedupe_history_accounted_for"
    DELIVERY_VALIDATION_COMPLETE = "delivery_validation_complete"
    INTEGRITY_VALIDATED = "integrity_validated"


class GateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gate: GenesisGate
    passed: bool
    reason: str = Field(min_length=1)
    checked_at: datetime | None = None


class DevelopmentArchive(BaseModel):
    model_config = ConfigDict(extra="forbid")

    archive_id: str = Field(min_length=1)
    role: Literal[DatastoreRole.HISTORICAL_ARCHIVE] = DatastoreRole.HISTORICAL_ARCHIVE
    integrity_verified: bool
    source_registry_version: str = Field(min_length=1)
    git_revision: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    archive_location: str = Field(min_length=1)


class ProductionDatastore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database_id: str = Field(min_length=1)
    role: Literal[DatastoreRole.PRODUCTION] = DatastoreRole.PRODUCTION
    fresh_empty: bool


class ProductionEpoch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    epoch_id: str = Field(min_length=1)
    epoch_number: int = Field(ge=1)
    git_revision: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    source_registry_version: str = Field(min_length=1)
    baseline_at: datetime
    previous_epoch_id: str | None = None
    preceding_archive_id: str | None = None
    delivery_authority_id: str | None = None


class ProductionGenesis(BaseModel):
    """A gated transition creating the first authoritative production state."""

    model_config = ConfigDict(extra="forbid")

    genesis_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    clank_id: str = Field(min_length=1)
    development_archive: DevelopmentArchive
    final_source_registry_version: str = Field(min_length=1)
    git_revision: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    classifier_version: str | None = None
    normaliser_version: str | None = None
    gates: list[GateResult] = Field(default_factory=list)
    production_database: ProductionDatastore
    production_epoch: ProductionEpoch
    baseline_mode: Literal["baseline"] = "baseline"
    novelty_delivery_enabled_during_baseline: bool = False
    first_seen_is_market_novelty: bool = False

    @model_validator(mode="after")
    def validate_authority_boundary(self) -> ProductionGenesis:
        if not self.development_archive.integrity_verified:
            raise ValueError("verified development archive is required")
        if not self.production_database.fresh_empty:
            raise ValueError("genesis requires a fresh empty production datastore")
        if self.production_epoch.epoch_number != 1:
            raise ValueError("Production Genesis must produce Production Epoch 1")
        if self.production_epoch.preceding_archive_id != self.development_archive.archive_id:
            raise ValueError("Epoch 1 must reference the development archive")
        if self.novelty_delivery_enabled_during_baseline:
            raise ValueError("ordinary novelty delivery must be disabled during baseline")
        return self

    @property
    def blockers(self) -> list[str]:
        return [result.reason for result in self.gates if not result.passed]

    @property
    def ready(self) -> bool:
        return (
            bool(self.gates) and not self.blockers and all(result.passed for result in self.gates)
        )
