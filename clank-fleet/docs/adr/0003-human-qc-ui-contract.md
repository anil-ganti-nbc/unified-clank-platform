# ADR 0003: Shared human-QC disposition and review queue contract

Status: Accepted

## Context

A static snapshot is insufficient for a collector haul that may contain 10,
100, or 1000+ reviewable findings. Operators need durable judgements without
losing evidence or being limited to the first visible page. The same feedback
semantics are useful across domains, while the fields around a finding are not
safely standardisable.

## Decision

Unified standardises `USEFUL`, `NOT USEFUL`, `FALSE POSITIVE`, and `OUT OF
STOCK`, plus durable feedback provenance, review-queue progression, full-run QC
semantics, and measurable progress. Review state is separate from disposition.
A reviewed item leaves the active queue and the next unreviewed eligible item
is exposed, but the underlying finding remains in history and search. Feedback
records are append-only in meaning and can be superseded by later feedback.

Domain Clanks own their surrounding UI and metadata. Event, Region, SKU,
Product, OEM, Game, Store, and similar concepts are not shared required
fields, and no domain table or tab layout becomes canonical.

Human feedback does not directly mutate domain truth or grant delivery or
production authority. Future ranking, suppression, source analysis, or ML may
consume it only through auditable, reversible, versioned, bounded, domain-owned
mechanisms. Collectors remain sensors. Human labels remain distinct from model
predictions. Legacy Clanks can advertise partial, planned, unsupported, or
unknown capability.

## Consequences

- Full-run review is behavioural; implementation may use paging, queue
  advancement, virtualisation, or an equivalent mechanism.
- `FALSE POSITIVE` is valuable diagnostic training signal but does not assert a
  root cause.
- `OUT OF STOCK` is time-scoped operator feedback, not permanent global
  unavailability.
- A durable feedback layer is required when a Clank claims support; this ADR
  does not choose a storage engine or implement child-Clank buttons.
- The shared runtime contract can be adopted dynamically without modifying any
  child Clank in this architecture task.

