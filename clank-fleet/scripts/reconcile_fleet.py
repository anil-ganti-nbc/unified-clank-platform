#!/usr/bin/env python3
"""Fleet reconciliation: compare inventories/clanks.yaml against reality.

Deliberately outside src/clank_fleet/ -- this is an operator/dev tool, not
part of the Stage 0.5 guarded API/CLI surface (see ARCHITECTURE_PRINCIPLES.md
and tests/test_architecture.py, which only scan src/). It shells out to git,
gh, and ssh rather than importing sqlite3/paramiko/etc., all of which are
forbidden imports under src/ for this stage.

Read-only. Never mutates the manifest, never mutates any target environment,
never restarts anything, never queries production secrets. Every remote
check is best-effort with a short timeout: an unreachable Hetzner or NAS
produces UNKNOWN for that surface, not a crash.

Usage:
    python3 scripts/reconcile_fleet.py [--workspace PATH] [--skip-remote] [--json]

    --workspace PATH   Local Mac Clank workspace to check against.
                        Defaults to the directory two levels above this
                        repo (i.e. sibling of unified-clank-platform),
                        which is where the fleet has lived historically.
                        Override for other machines/checkouts.
    --skip-remote       Skip Hetzner/NAS SSH checks (GitHub + local only).
    --json               Emit machine-readable JSON instead of the table.

Exit code is always 0 -- this reports discrepancies, it does not gate CI.
Reconciliation status is data, not a pass/fail signal for this script itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]  # clank-fleet/
MANIFEST_PATH = REPO_ROOT / "inventories" / "clanks.yaml"

HETZNER_HOST = "hetzner"  # expects an SSH config alias; see project docs
NAS_HOST = "nas"  # expects an SSH config alias; see project docs
REMOTE_TIMEOUT_SECONDS = 8


def _run(cmd: list[str], timeout: float = REMOTE_TIMEOUT_SECONDS) -> tuple[bool, str]:
    """Run a command, returning (ok, stdout-or-error). Never raises."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout or "").strip()
        return True, result.stdout.strip()
    except FileNotFoundError:
        return False, f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s"
    except Exception as exc:  # pragma: no cover - defensive only
        return False, f"unexpected error: {exc}"


@dataclass
class SurfaceResult:
    status: str  # PRESENT | MISSING | UNKNOWN | INTENTIONALLY_ABSENT
    detail: str = ""


@dataclass
class ClankReconciliation:
    clank_id: str
    display_name: str
    state_class: str
    local: SurfaceResult = field(default_factory=lambda: SurfaceResult("UNKNOWN"))
    github: SurfaceResult = field(default_factory=lambda: SurfaceResult("UNKNOWN"))
    hetzner: SurfaceResult = field(default_factory=lambda: SurfaceResult("UNKNOWN"))
    nas: SurfaceResult = field(default_factory=lambda: SurfaceResult("UNKNOWN"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "clank_id": self.clank_id,
            "display_name": self.display_name,
            "state_class": self.state_class,
            "local": vars(self.local),
            "github": vars(self.github),
            "hetzner": vars(self.hetzner),
            "nas": vars(self.nas),
        }


def load_manifest() -> list[dict[str, Any]]:
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    clanks = data.get("clanks")
    if not isinstance(clanks, list):
        raise ValueError(f"{MANIFEST_PATH}: expected top-level 'clanks' list")
    return clanks


def check_local(entry: dict[str, Any], workspace: Path) -> SurfaceResult:
    rel = entry.get("expected_local_directory")
    if not rel:
        return SurfaceResult("INTENTIONALLY_ABSENT", "no local directory expected")
    path = workspace / rel
    if not path.is_dir():
        return SurfaceResult("MISSING", f"expected at {path}")
    if not (path / ".git").exists():
        return SurfaceResult("PRESENT", f"{path} (not a git checkout)")
    ok, head = _run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"])
    if not ok:
        return SurfaceResult("PRESENT", f"{path} (HEAD unreadable: {head})")
    ok2, dirty = _run(["git", "-C", str(path), "status", "--porcelain"])
    dirty_note = "clean" if (ok2 and not dirty) else "dirty" if ok2 else "dirty-status-unknown"
    return SurfaceResult("PRESENT", f"HEAD {head}, {dirty_note}")


def check_github(entry: dict[str, Any]) -> SurfaceResult:
    url = entry.get("repository_url", "")
    slug = url.rstrip("/").split("github.com/")[-1] if "github.com/" in url else None
    if not slug:
        return SurfaceResult("UNKNOWN", "no repository_url")
    ok, out = _run(["gh", "api", f"repos/{slug}", "--jq", ".pushed_at"])
    if not ok:
        # gh unavailable or repo not found -- try unauthenticated REST as a fallback signal only
        return SurfaceResult("UNKNOWN", f"gh api failed: {out}")
    return SurfaceResult("PRESENT", f"last pushed {out}")


def check_hetzner(entry: dict[str, Any], skip_remote: bool) -> SurfaceResult:
    if "hetzner" not in (entry.get("expected_deployment_targets") or []):
        return SurfaceResult("INTENTIONALLY_ABSENT", "not an expected Hetzner deployment")
    if skip_remote:
        return SurfaceResult("UNKNOWN", "remote checks skipped")
    clank_id = entry["clank_id"]
    # Known layout precedents, in the order they were adopted over time:
    # legacy /opt/<id>, direct /home/deploy/<id> (e.g. free-game-tracker),
    # /home/deploy/staging/<id> (current convention), /home/deploy/experimental/<id>.
    # Check all four; report whichever answers -- do not assume any one
    # convention is universal, this fleet has used all of them.
    candidates = (
        f"/opt/{clank_id}",
        f"/home/deploy/{clank_id}",
        f"/home/deploy/staging/{clank_id}",
        f"/home/deploy/experimental/{clank_id}",
    )
    # Exit 0 unconditionally: the loop's `[ -d ] && echo` pattern means the
    # remote shell's exit status reflects only the *last* candidate's test,
    # not whether an earlier one matched. Presence is read from stdout
    # content, never from the SSH/remote exit code.
    ok, out = _run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", HETZNER_HOST,
         "for p in " + " ".join(candidates) + "; do [ -d \"$p\" ] && echo FOUND:$p; done; exit 0"],
        timeout=REMOTE_TIMEOUT_SECONDS,
    )
    if not ok:
        return SurfaceResult("UNKNOWN", f"ssh {HETZNER_HOST} unreachable or failed: {out}")
    if "FOUND:" not in out:
        return SurfaceResult("MISSING", "not found under staging/experimental/opt")
    return SurfaceResult("PRESENT", out.replace("FOUND:", "").strip())


def check_nas(entry: dict[str, Any], skip_remote: bool) -> SurfaceResult:
    if "nas" not in (entry.get("expected_deployment_targets") or []):
        return SurfaceResult("INTENTIONALLY_ABSENT", "not an expected NAS deployment")
    if skip_remote:
        return SurfaceResult("UNKNOWN", "remote checks skipped")
    clank_id = entry["clank_id"]
    path = f"/volume2/clank/{clank_id}"
    ok, out = _run(
        ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", NAS_HOST,
         f"[ -d '{path}' ] && echo FOUND || echo ABSENT"],
        timeout=REMOTE_TIMEOUT_SECONDS,
    )
    if not ok:
        return SurfaceResult("UNKNOWN", f"ssh {NAS_HOST} unreachable or failed: {out}")
    if "FOUND" in out:
        return SurfaceResult("PRESENT", path)
    return SurfaceResult("MISSING", f"not found at {path}")


def reconcile(workspace: Path, skip_remote: bool) -> list[ClankReconciliation]:
    results = []
    for entry in load_manifest():
        r = ClankReconciliation(
            clank_id=entry["clank_id"],
            display_name=entry.get("display_name", entry["clank_id"]),
            state_class=entry.get("state_class", "unknown"),
        )
        if entry.get("state_class") == "deprecated":
            r.local = SurfaceResult("INTENTIONALLY_ABSENT", "deprecated entry")
            r.github = check_github(entry)  # still worth confirming it hasn't been revived
            r.hetzner = SurfaceResult("INTENTIONALLY_ABSENT", "deprecated entry")
            r.nas = SurfaceResult("INTENTIONALLY_ABSENT", "deprecated entry")
            results.append(r)
            continue
        r.local = check_local(entry, workspace)
        r.github = check_github(entry)
        r.hetzner = check_hetzner(entry, skip_remote)
        r.nas = check_nas(entry, skip_remote)
        results.append(r)
    return results


def render_table(results: list[ClankReconciliation]) -> str:
    lines = []
    for r in results:
        lines.append(f"{r.clank_id.upper()}  ({r.display_name}, state_class={r.state_class})")
        for label, surf in (
            ("  local  ", r.local),
            ("  github ", r.github),
            ("  hetzner", r.hetzner),
            ("  nas    ", r.nas),
        ):
            lines.append(f"{label}: {surf.status:<22} {surf.detail}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=REPO_ROOT.parents[1],  # unified-clank-platform/.. == Clank base on this machine
        help="Local Clank workspace directory to check against.",
    )
    parser.add_argument("--skip-remote", action="store_true", help="Skip Hetzner/NAS SSH checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    args = parser.parse_args()

    results = reconcile(args.workspace, args.skip_remote)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print(render_table(results))

    return 0


if __name__ == "__main__":
    sys.exit(main())
