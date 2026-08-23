# clank-fleet

Fleet control plane shell, API, and CLI for the Unified Clank Infrastructure.

**Stage 0.5 — skeleton + hardening. No production behavior.**

## Layout

```
src/clank_fleet/
  fleet_api/     # FastAPI factory + 501 route stubs
  operations/    # FleetControlAdapter protocol / abstract adapter
  cli.py         # Typer CLI (ops exit 78)
compose/         # NON-PRODUCTION TEMPLATE files only
inventories/     # clanks.yaml -- authoritative fleet manifest
                 # clanks.example.yaml -- draft schema reference, keep as-is
scripts/         # operator tooling outside the guarded src/ tree
                 # (reconcile_fleet.py: manifest vs. GitHub/Mac/Hetzner/NAS)
docs/            # architecture notes, ADRs, runbook templates
tests/           # includes architecture guardrails
```

## Fleet manifest

`inventories/clanks.yaml` is the fleet's authoritative, machine-readable
identity registry -- see its header comment for the full field reference.
Compiled 2026-08-18 from an independent cross-reference of GitHub, this
Mac, Hetzner, and the NAS (not from `ls` on any one directory -- see
Prime Directive A in the originating investigation). Run
`scripts/reconcile_fleet.py` to check it against current reality; do not
hand-edit it to make a reconciliation mismatch disappear.

## Commands

```bash
# from monorepo root
make bootstrap
clank version
clank status          # exits 78
uvicorn clank_fleet.fleet_api.app:create_app --factory --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/api/v1/system/ping
```

## Non-goals

No databases, Docker control, Tailscale, real auth, ingestion, or scrapers.

See `../../ARCHITECTURE_PRINCIPLES.md` and `../../DEPENDENCIES.md`.
