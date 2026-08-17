# scripts/

Operator/dev tooling that lives outside `src/clank_fleet/` on purpose: it is
not part of the Stage 0.5 guarded API/CLI surface, and it needs to shell out
to `git`, `gh`, and `ssh` -- imports that `tests/test_architecture.py`
correctly forbids under `src/` for this stage (no direct `paramiko`, no
production behavior in placeholder modules).

## `reconcile_fleet.py`

Compares `inventories/clanks.yaml` (the authoritative fleet manifest)
against reality: this Mac's local checkouts, GitHub, Hetzner, and the NAS.
Read-only. Never mutates the manifest or any target environment.

```bash
python3 scripts/reconcile_fleet.py                  # table output
python3 scripts/reconcile_fleet.py --json            # machine-readable
python3 scripts/reconcile_fleet.py --skip-remote     # local + GitHub only, no SSH
python3 scripts/reconcile_fleet.py --workspace /path/to/other/checkout
```

Requires the `[dev]` extra (`pyyaml`) from `make bootstrap`. Hetzner/NAS
checks expect SSH config aliases named `hetzner` and `nas`; if those aren't
configured on the machine running this, remote checks report `UNKNOWN` for
that surface rather than failing.

This is the mechanism Prime Directive A depends on: "local workspace
discovery is not fleet discovery." A Clank present in the manifest but
absent from every surface below `MISSING`; a Clank present on disk but not
in the manifest is a gap in the manifest itself, not the fleet -- add it.

Exit code is always 0. This reports discrepancies as data; it is not a CI
gate. Nothing here should ever be run as an automated/scheduled job without
an operator reading the output -- it is a census tool, not a monitor.
