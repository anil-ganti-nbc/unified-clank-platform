# ADR 0001: Keep exploratory state out of first production history

Status: Accepted

Under-development Clanks must not promote an exploratory datastore directly
into their first authoritative production database. Expansion is expected to
produce useful hits, duplicates, stale discoveries, identity collisions, and
classification errors. That contamination is valuable for learning, but it is
not authoritative operational history.

Production Genesis archives the corpus, freezes the validated rules and source
registry, creates a fresh production datastore, and baselines it without a
novelty alert avalanche. A database reset cannot establish market novelty:
`first_seen_in_new_production_db` is not `new_to_market`. Delivery and dedupe
history must be retained or explicitly reconciled. Mature Clanks are not
mechanically reset; they use their normal epoch and source lifecycle controls.

Unified owns these contracts and gates only. Corpus intelligence, autonomous
approval, and Diagnostic Clank investigation remain external/advisory concerns.
