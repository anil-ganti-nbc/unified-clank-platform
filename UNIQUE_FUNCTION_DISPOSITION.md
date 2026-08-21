# Unified Clank Platform function disposition

Status: **FROZEN SUPERSESSION CANDIDATE — REVIEW REQUIRED — NOT CANONICAL.**
Supersession is not accepted or complete, and this repository must not be
promoted while the governance decision remains open.
Compared: 2026-08-21 against the current `diagnostic-clank` Phase 0 branch.

| Area | Evidence | Proposed disposition |
|---|---|---|
| `clank-runtime` contracts | Diagnostic contains the common contracts plus actions, adapters, delivery, desktop cache, failure/fallback, ledger, lifecycle, machine, telemetry, diagnostic, knowledge, and registry modules absent here. Shared files have evolved. | Retire this older copy after contract/API review confirms no incompatible consumer. Do not merge directories blindly. |
| `clank-fleet` | Diagnostic contains the fleet ledger, adapters, registry, inventory validation, fixtures, and expanded API/CLI tests absent here. | Retire this older copy; the diagnostic implementation is the proposed migration target. |
| `clank-desktop` | Diagnostic contains the shared tree plus an inbox implementation absent here. | Retire after a native packaging/entry-point comparison. |
| portability templates | Path comparison found no differences in the reviewed templates. | Retain in Diagnostic; remove duplication only after supersession is accepted. |
| root Makefile / dependency rationale | Root Makefile and dependency rationale are shared or substantially duplicated. | Retain the maintained Diagnostic copies. |
| historical architecture documents | This repository contains Stage 0.5 historical rationale and reviewed architecture text. | Preserve as read-only history or migrate links into governance; do not treat it as current authority. |
| Fleet API action route | Present only as a 501/non-production stub in this prototype. | No unique production behavior to migrate. |

No unique production runtime behavior was identified by the reviewed path and
diff comparison. That is not yet archival approval. Before accepting
supersession, a reviewer must record exact comparison SHAs, check packaging and
entry points, search external consumers/imports, preserve historical documents,
and approve archive/branch-protection/ownership treatment. Until then this
repository remains a frozen supersession candidate.
