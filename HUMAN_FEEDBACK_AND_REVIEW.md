# Shared Human Feedback and Review Contract

Status: Accepted architecture contract for reviewable findings

This document defines the portable human-QC semantics for Unified Clank. It
does not prescribe a shared table, tab layout, domain schema, persistence
technology, or child-Clank implementation.

## Standard dispositions

Every Clank UI that surfaces reviewable findings should expose:

`[ USEFUL ]  [ NOT USEFUL ]  [ FALSE POSITIVE ]  [ OUT OF STOCK ]`

- **USEFUL** means useful or actionable to the operator. It does not mean
  verified, authoritative, new-to-market, delivered, or factually perfect.
- **NOT USEFUL** means the finding may be valid but was not editorially or
  operationally useful. It is distinct from a false positive.
- **FALSE POSITIVE** means the finding should not have qualified as surfaced.
  The label does not assert whether identity, classification, freshness,
  source pollution, duplicate handling, or normalisation caused it.
- **OUT OF STOCK** means the item was unavailable at review time. It does not
  mean globally discontinued or permanently unavailable.

Human disposition is operator judgement, not model prediction and not domain
truth. A later model may produce predicted probabilities, but those remain
distinct from the human-labelled disposition.

## Review queue behaviour

Review state is separate from disposition. The shared states are
`UNREVIEWED`, `REVIEWED`, `DEFERRED`, and `DISMISSED`. A disposition click must:

1. durably persist a record attached to the stable finding identity;
2. record actor, time, channel, and available provenance;
3. mark the item reviewed;
4. remove it from the active review queue without deleting the finding;
5. immediately expose the next unreviewed eligible item;
6. retain the reviewed item in history and search; and
7. update measurable progress counters.

The operator must be able to QC the entire eligible collector haul, including
items beyond the first visible page, through paging, queue advancement,
virtualisation, or an equivalent mechanism. Counts must be explicit: if a
Clank cannot measure a count, it reports unknown rather than fabricating zero.

Stable identity is owned by the domain and may use `finding_id`, `event_id`,
`lead_id`, and `run_id` as appropriate. It must never be only a row number or
temporary screen position. Feedback history is append-only in meaning: later
judgement may supersede earlier judgement without destroying it.

## Domain-owned presentation

Only the four dispositions, review state, persistence/history, next-item
behaviour, full-run semantics, and feedback provenance are shared. Surrounding
fields remain domain-specific:

| Clank | Illustrative surrounding fields |
|---|---|
| Watch Clank | Event, Region, SKU |
| OEM Radar | Product, OEM, Region |
| Smartphone | Device, Source, Region |
| Free Game Tracker | Game, Store, Offer type |

These are examples, not mandatory shared columns. No Clank tab layout is
canonical.

## Illustrative, non-binding flow

```text
Finding 41 of 123
Event: ...   Region: ...   Source: ...

[ USEFUL ] [ NOT USEFUL ] [ FALSE POSITIVE ] [ OUT OF STOCK ]

Reviewed: 40 / 123
```

After `FALSE POSITIVE`, the system stores feedback, marks Finding 41 reviewed,
preserves it in history, updates progress, and presents Finding 42. Event and
Region are illustrative only.

## Authority and future use

Feedback must survive page reload, application restart, collector rerun,
rebaseline, ProductionEpoch transitions, and Production Genesis where the
Clank capability supports it. It must not directly mutate authoritative
external-state truth: `OUT OF STOCK` does not globally set availability false,
`FALSE POSITIVE` does not delete source data, and `USEFUL` does not grant
production or delivery authority.

Feedback may later inform ranking, review ordering, bounded suppression, source
quality analysis, enrichment priority, collection planning, or ML training.
Any such use must be auditable, reversible, versioned, bounded, and owned by
the domain. Collectors remain sensors; feedback must not silently create
permanent blind spots. Repeated false positives are valuable input to
Diagnostic Clank and future ClankOps investigation, but the button itself is
not a root-cause classification and Diagnostic Clank remains advisory and
read-only.

## Capability advertisement

The shared runtime contract exposes `HUMAN_QC_FEEDBACK` with support values
`SUPPORTED_NATIVE`, `SUPPORTED_ADAPTER`, `PARTIAL`, `PLANNED`, `UNSUPPORTED`,
`NOT_APPLICABLE`, and `UNKNOWN`. Legacy Clanks may advertise partial or
unsupported capability. Future Clanks should treat the capability as a day-one
default unless clearly not applicable; no legacy representation is invalidated.

