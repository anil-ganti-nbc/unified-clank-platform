from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from clank_runtime.contracts.genesis import (
    DatastoreRole,
    DevelopmentArchive,
    GateResult,
    GenesisGate,
    ProductionDatastore,
    ProductionEpoch,
    ProductionGenesis,
)


def make_genesis(**changes):
    archive = DevelopmentArchive(
        archive_id="archive-1",
        integrity_verified=True,
        source_registry_version="src-2",
        git_revision="abc123",
        schema_version="3",
        archive_location="archive://1",
    )
    data = dict(
        clank_id="future-clank",
        development_archive=archive,
        final_source_registry_version="src-2",
        git_revision="abc123",
        schema_version="3",
        production_database=ProductionDatastore(database_id="prod-1", fresh_empty=True),
        production_epoch=ProductionEpoch(
            epoch_id="epoch-1",
            epoch_number=1,
            git_revision="abc123",
            schema_version="3",
            source_registry_version="src-2",
            baseline_at=datetime.now(UTC),
            preceding_archive_id="archive-1",
        ),
        gates=[
            GateResult(
                gate=GenesisGate.DEVELOPMENT_ARCHIVE_VERIFIED,
                passed=True,
                reason="verified",
            )
        ],
    )
    data.update(changes)
    return ProductionGenesis(**data)


def test_development_role_has_no_production_novelty_authority():
    assert DatastoreRole.DEVELOPMENT_CORPUS != DatastoreRole.PRODUCTION
    assert make_genesis().first_seen_is_market_novelty is False


def test_genesis_requires_verified_archive_and_fresh_database():
    with pytest.raises(ValidationError):
        make_genesis(production_database=ProductionDatastore(database_id="x", fresh_empty=False))


def test_baseline_and_epoch_one_are_explicit():
    genesis = make_genesis()
    assert genesis.baseline_mode == "baseline"
    assert genesis.novelty_delivery_enabled_during_baseline is False
    assert genesis.production_epoch.epoch_number == 1
    assert genesis.production_epoch.preceding_archive_id == genesis.development_archive.archive_id


def test_failed_gate_reports_exact_blocker():
    genesis = make_genesis(
        gates=[
            GateResult(
                gate=GenesisGate.SERIOUS_IDENTITY_ERRORS_RESOLVED,
                passed=False,
                reason="two unresolved collisions",
            )
        ]
    )
    assert genesis.ready is False
    assert genesis.blockers == ["two unresolved collisions"]


def test_soak_duration_is_not_a_genesis_field():
    assert "soak_duration" not in ProductionGenesis.model_fields
