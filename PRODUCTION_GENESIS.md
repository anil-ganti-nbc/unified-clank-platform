# Production Genesis

Production Genesis is the controlled transition from an exploratory
development corpus to a Clank's first authoritative production state.

The lifecycle is: build → foundation soak → source expansion → expansion soak
→ corpus analysis → classification/identity/normalisation fixes → final
validation soak → freeze the final source set and rules → quiesce and archive
the development datastore → create a fresh empty production datastore → run a
baseline → validate novelty and delivery → Production Epoch 1.

The development corpus is sacrificial in operational role, not disposable. It
must be quiesced, integrity-checked, archived with authoritative evidence, Git
revision, schema, source registry, classifier/normaliser revisions, checksum,
and location. It becomes read-only historical evidence for replay, ClankOps,
and Diagnostic Clank; it is never live production state.

Only the frozen, validated source registry participates in genesis. It should
preserve both authoritative-state coverage and early-signal/specialist coverage
where the domain benefits from it. Primary sources remain authoritative
product/state evidence; specialist sources remain discovery or lead evidence.
Initial soak may be authoritative-only, but expansion should actively seek
specialist sources rather than making the initial baseline an official-only
production design. Each adapter declares what may cross the boundary:
rules, fixtures, identities/aliases with provenance, feedback, and delivery /
dedupe history where supported. Experimental observations, stale cursors,
temporary events, soak health, and experimental queues are not copied blindly.

The first production crawl is `BASELINE_MODE`. First-seen membership is not
market novelty, so ordinary novelty delivery is disabled. Independently
verified freshness may still be represented. Delivery and dedupe authority must
be preserved separately or the adapter must explicitly report that limitation.

The runtime contract is `clank_runtime.contracts.genesis.ProductionGenesis`.
It requires a verified archive, a fresh production datastore, and Epoch 1; gate
failures retain inspectable reasons rather than collapsing to `ready = false`.
Fleet membership is dynamic and legacy Clanks may advertise partial or
unsupported capability. Motherclank/ClankOps intelligence and Diagnostic Clank
advisory decisions remain outside Unified.

This does not require destructive recreation for a mature production Clank
adding a well-understood source. Such changes use source lifecycle, shadow soak,
baseline firewall, and controlled ProductionEpoch transitions.
