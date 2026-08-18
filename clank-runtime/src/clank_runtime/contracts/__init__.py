"""Draft contracts for runtime identity, operational state, and related models.

These are Stage 0.5 draft contracts. They are not authoritative final schemas.
Semantic fields are stable; additive changes require a contract version bump.
"""

from __future__ import annotations

from clank_runtime.contracts.confidence import (
    CORROBORATION,
    ENTITY_CERTAINTY,
    EVIDENCE_STRENGTH,
    FRESHNESS,
    INGESTION_QUALITY,
    KNOWN_CONFIDENCE_DIMENSIONS,
    PARSER_QUALITY,
    SOURCE_RELIABILITY,
)
from clank_runtime.contracts.constitution import (
    AgentClaim,
    ClaimState,
    DeliveryRecord,
    DeliveryState,
    EpistemicStatus,
    ExecutionProvenance,
    Interpretation,
    ObservationHealth,
    ObservationResult,
    PipelineStage,
    RawEvidence,
    StageRecord,
)
from clank_runtime.contracts.enums import (
    IngestionState,
    OperationalState,
    ReleaseChannel,
)
from clank_runtime.contracts.events import EventEnvelope
from clank_runtime.contracts.genesis import (
    DatastoreRole,
    DevelopmentArchive,
    GateResult,
    GenesisCapability,
    GenesisGate,
    ProductionDatastore,
    ProductionEpoch,
    ProductionGenesis,
)
from clank_runtime.contracts.health import CollectorSummary, HealthPayload
from clank_runtime.contracts.identity import RuntimeIdentity
from clank_runtime.contracts.operations import (
    OperationResult,
    OperationState,
    OperationType,
)
from clank_runtime.contracts.sources import (
    CoverageFact,
    EvidenceClaim,
    EvidenceKind,
    SourceCapability,
    SourceDescriptor,
    SourceRole,
)

__all__ = [
    "RuntimeIdentity",
    "OperationalState",
    "ReleaseChannel",
    "IngestionState",
    "HealthPayload",
    "CollectorSummary",
    "OperationResult",
    "OperationState",
    "OperationType",
    "EventEnvelope",
    "DatastoreRole",
    "DevelopmentArchive",
    "GenesisCapability",
    "GenesisGate",
    "GateResult",
    "ProductionDatastore",
    "ProductionEpoch",
    "ProductionGenesis",
    "SourceRole",
    "SourceCapability",
    "EvidenceKind",
    "SourceDescriptor",
    "CoverageFact",
    "EvidenceClaim",
    "EpistemicStatus",
    "ObservationHealth",
    "ObservationResult",
    "PipelineStage",
    "StageRecord",
    "DeliveryState",
    "DeliveryRecord",
    "ExecutionProvenance",
    "RawEvidence",
    "Interpretation",
    "ClaimState",
    "AgentClaim",
    "KNOWN_CONFIDENCE_DIMENSIONS",
    "SOURCE_RELIABILITY",
    "EVIDENCE_STRENGTH",
    "CORROBORATION",
    "FRESHNESS",
    "PARSER_QUALITY",
    "INGESTION_QUALITY",
    "ENTITY_CERTAINTY",
]
