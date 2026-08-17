"""Tests for the authoritative fleet manifest and its reconciliation tool.

Schema/content checks on inventories/clanks.yaml, plus unit tests for
scripts/reconcile_fleet.py's pure logic (manifest loading, local-directory
checking). Deliberately does not exercise the real GitHub/Hetzner/NAS
network paths here -- those are best-effort and environment-dependent by
design; see scripts/README.md.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "inventories" / "clanks.yaml"
SCRIPT_PATH = ROOT / "scripts" / "reconcile_fleet.py"

REQUIRED_FIELDS = {
    "clank_id",
    "display_name",
    "primary_purpose",
    "project_type",
    "repository_url",
    "expected_local_directory",
    "native_client_support",
    "expected_deployment_targets",
    "state_class",
    "lifecycle_maturity",
}
VALID_STATE_CLASSES = {"production", "experimental", "deferred", "deprecated"}
VALID_DEPLOYMENT_TARGETS = {"hetzner", "nas", "mac-field-test"}


def _load_manifest() -> dict:
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def _import_reconcile_module():
    spec = importlib.util.spec_from_file_location("reconcile_fleet", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # dataclass() needs this registered before exec
    spec.loader.exec_module(module)
    return module


def test_manifest_parses_and_has_clanks_list() -> None:
    data = _load_manifest()
    assert isinstance(data.get("clanks"), list)
    assert len(data["clanks"]) > 0


def test_every_entry_has_required_fields() -> None:
    for entry in _load_manifest()["clanks"]:
        missing = REQUIRED_FIELDS - entry.keys()
        assert not missing, f"{entry.get('clank_id', '?')} missing fields: {missing}"


def test_clank_ids_are_unique() -> None:
    ids = [entry["clank_id"] for entry in _load_manifest()["clanks"]]
    assert len(ids) == len(set(ids)), "duplicate clank_id in manifest"


def test_clank_ids_match_expected_local_directory_when_present() -> None:
    for entry in _load_manifest()["clanks"]:
        local_dir = entry.get("expected_local_directory")
        if local_dir is not None:
            assert local_dir == entry["clank_id"], (
                f"{entry['clank_id']}: expected_local_directory {local_dir!r} "
                "should match clank_id unless there's a documented reason it diverges"
            )


def test_repository_urls_point_at_github() -> None:
    for entry in _load_manifest()["clanks"]:
        assert entry["repository_url"].startswith(
            "https://github.com/anil-ganti-nbc/"
        ), entry["clank_id"]


def test_state_class_is_valid_enum_value() -> None:
    for entry in _load_manifest()["clanks"]:
        assert entry["state_class"] in VALID_STATE_CLASSES, (
            f"{entry['clank_id']}: unknown state_class {entry['state_class']!r}"
        )


def test_deployment_targets_are_valid_enum_values() -> None:
    for entry in _load_manifest()["clanks"]:
        for target in entry["expected_deployment_targets"]:
            assert target in VALID_DEPLOYMENT_TARGETS, (
                f"{entry['clank_id']}: unknown deployment target {target!r}"
            )


def test_deprecated_entries_have_no_expected_deployment_targets() -> None:
    for entry in _load_manifest()["clanks"]:
        if entry["state_class"] == "deprecated":
            assert entry["expected_deployment_targets"] == [], entry["clank_id"]
            assert entry["expected_local_directory"] is None, entry["clank_id"]


def test_no_head_sha_or_health_fields_hand_maintained() -> None:
    """Prime Directive: don't hand-maintain transient state that reconciliation discovers."""
    forbidden_keys = {"head_sha", "head", "revision", "health", "last_run", "git_sha"}
    for entry in _load_manifest()["clanks"]:
        present = forbidden_keys & entry.keys()
        assert not present, f"{entry['clank_id']}: manifest should not hand-maintain {present}"


# ---------------------------------------------------------------------------
# reconcile_fleet.py pure-logic unit tests (no real network/SSH)
# ---------------------------------------------------------------------------

def test_reconcile_script_loads_real_manifest() -> None:
    module = _import_reconcile_module()
    clanks = module.load_manifest()
    assert any(c["clank_id"] == "watch-clank" for c in clanks)


def test_check_local_reports_missing_for_absent_directory(tmp_path) -> None:
    module = _import_reconcile_module()
    entry = {"expected_local_directory": "does-not-exist"}
    result = module.check_local(entry, tmp_path)
    assert result.status == "MISSING"


def test_check_local_reports_intentionally_absent_when_none_expected(tmp_path) -> None:
    module = _import_reconcile_module()
    entry = {"expected_local_directory": None}
    result = module.check_local(entry, tmp_path)
    assert result.status == "INTENTIONALLY_ABSENT"


def test_check_local_reports_present_and_clean_for_real_git_checkout(tmp_path) -> None:
    module = _import_reconcile_module()
    repo = tmp_path / "some-clank"
    repo.mkdir()
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)
    (repo / "README.md").write_text("hi", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    entry = {"expected_local_directory": "some-clank"}
    result = module.check_local(entry, tmp_path)
    assert result.status == "PRESENT"
    assert "clean" in result.detail


def test_check_hetzner_intentionally_absent_when_not_targeted() -> None:
    module = _import_reconcile_module()
    entry = {"clank_id": "x", "expected_deployment_targets": []}
    result = module.check_hetzner(entry, skip_remote=True)
    assert result.status == "INTENTIONALLY_ABSENT"


def test_check_hetzner_unknown_when_remote_skipped() -> None:
    module = _import_reconcile_module()
    entry = {"clank_id": "x", "expected_deployment_targets": ["hetzner"]}
    result = module.check_hetzner(entry, skip_remote=True)
    assert result.status == "UNKNOWN"


def test_check_nas_intentionally_absent_when_not_targeted() -> None:
    module = _import_reconcile_module()
    entry = {"clank_id": "x", "expected_deployment_targets": []}
    result = module.check_nas(entry, skip_remote=True)
    assert result.status == "INTENTIONALLY_ABSENT"
