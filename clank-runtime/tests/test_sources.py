from clank_runtime.contracts.sources import (
    CoverageFact,
    EvidenceClaim,
    EvidenceKind,
    SourceCapability,
    SourceDescriptor,
    SourceRole,
)


def test_primary_and_specialist_roles_and_capabilities_are_independent():
    primary = SourceDescriptor(
        source_id="oem", role=SourceRole.PRIMARY_OFFICIAL, region="US", surface="catalogue",
        capabilities={SourceCapability.AUTHORITATIVE_SPECS}, authority_level="authoritative",
        lifecycle_state="production",
    )
    specialist = SourceDescriptor(
        source_id="press",
        role=SourceRole.SPECIALIST_EDITORIAL,
        region="global",
        surface="editorial",
        capabilities={SourceCapability.EARLY_SIGNAL, SourceCapability.LEAK_SIGNAL},
        authority_level="non_authoritative", lifecycle_state="experimental",
    )
    assert primary.role != specialist.role
    assert SourceCapability.AUTHORITATIVE_SPECS not in specialist.capabilities
    assert SourceCapability.LEAK_SIGNAL in specialist.capabilities


def test_specialist_can_create_lead_without_authoritative_overwrite():
    claim = EvidenceClaim(
        claim_id="lead-1", source_id="press", source_role=SourceRole.SPECIALIST_EDITORIAL,
        kind=EvidenceKind.EARLY_SIGNAL, subject_id="future-phone", claim={"model": "X"},
    )
    assert not claim.can_update_authoritative_state()


def test_verified_claim_may_be_explicitly_authorized():
    claim = EvidenceClaim(
        claim_id="confirmed-1", source_id="oem", source_role=SourceRole.PRIMARY_OFFICIAL,
        kind=EvidenceKind.AUTHORITATIVE_STATE, subject_id="phone", independently_verified=True,
        authoritative_state_update_allowed=True,
    )
    assert claim.can_update_authoritative_state()


def test_coverage_is_region_surface_and_role_specific():
    fact = CoverageFact(
        domain="devices", entity="Citizen", region="JP", surface="support",
        source_role=SourceRole.REGIONAL_OFFICIAL, source_id="jp-support",
        operationally_healthy=True, intelligence_coverage_sufficient=None,
    )
    assert (fact.region, fact.surface, fact.source_role) == (
        "JP", "support", SourceRole.REGIONAL_OFFICIAL
    )
    assert fact.intelligence_coverage_sufficient is None
