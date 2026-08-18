# clank-runtime

Shared runtime **contracts and interfaces** for Unified Clank.

**Stage 0.5 — models and protocols only.**

## Owns

- Runtime identity, health payload, operation result, event envelope
- Operational / release / ingestion state enums
- Confidence dimension *names* (not scoring)
- Protocol interfaces for config, health, metadata, events, lifecycle, operations
- Shared human-QC disposition, review-queue, provenance, and capability contracts

## Does not own

Scraping, collectors, schedulers, domain models, persistence, outbox writers.

## Install

```bash
pip install -e ".[dev]"
pytest -q
```

## Contract versions

Independent of package version (`0.0.1.dev0`). See `clank_runtime.version`.

Authoritative architecture: `unified-clank-architecture-v2.1-reviewed.md` (Amendment 2).
Human feedback contract: `../HUMAN_FEEDBACK_AND_REVIEW.md`.
