from datetime import UTC, datetime

from clank_runtime.contracts.constitution import (
    AgentClaim,
    ClaimState,
    DeliveryState,
    EpistemicStatus,
    Interpretation,
    ObservationHealth,
    ObservationResult,
    PipelineStage,
    RawEvidence,
    StageRecord,
)


def test_unknown_is_valid_and_unmeasured_is_not_zero():
    stage = StageRecord(stage=PipelineStage.IDENTIFY)
    assert stage.status is EpistemicStatus.UNKNOWN
    assert stage.succeeded is None


def test_unhealthy_zero_cannot_advance_absence():
    observation = ObservationResult(
        source_id="catalogue",
        observed_at=datetime.now(UTC),
        health=ObservationHealth.UNHEALTHY,
        result_count=0,
    )
    assert observation.can_advance_absence() is False


def test_healthy_zero_can_be_considered_by_domain_semantics():
    observation = ObservationResult(
        source_id="catalogue",
        observed_at=datetime.now(UTC),
        health=ObservationHealth.HEALTHY,
        result_count=0,
    )
    assert observation.can_advance_absence() is True


def test_delivery_is_separate_from_event_stage():
    assert DeliveryState.EVENT_CREATED != DeliveryState.DELIVERY_SUCCEEDED


def test_raw_evidence_and_interpretation_are_separate_and_versioned():
    raw = RawEvidence(
        evidence_id="raw-1",
        captured_at=datetime.now(UTC),
        content_hash="hash",
        source_reference="https://example.test",
    )
    interpretation = Interpretation(
        interpretation_id="interpretation-2",
        evidence_id=raw.evidence_id,
        version=2,
        derived_at=datetime.now(UTC),
        supersedes_interpretation_id="interpretation-1",
    )
    assert raw.immutable is True
    assert interpretation.evidence_id == raw.evidence_id


def test_agent_identity_is_provenance_not_verification():
    claim = AgentClaim(claim_id="claim-1", claimant="codex", statement="possible source gap")
    assert claim.state is ClaimState.REPORTED
