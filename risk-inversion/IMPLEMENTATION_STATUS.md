# Implementation status — 2026-09-23

## Implemented in source

- Holding Risk & Inversion control-plane contracts.
- Risk, inversion, runtime intent, authorization and human-override models.
- Deterministic intent policy checks with expiry and kill-switch semantics.
- Golden-case comparator.
- Evidence-gated control promotion helper.
- Hash-chained audit-event contract with verification.
- Cue → Tag → Content memory reconstruction contract with pruning.
- AI Register schema.
- Risk Register schema.
- Brand risk-liaison contract.
- SOP-016 through SOP-020 definitions.

## Not yet proven LIVE

These require deployment/integration evidence and therefore remain GAP/EXISTS until proved:

- real credential broker issuing short-lived credentials
- enforcement of authorization on every consequential runtime action
- distributed/global kill switch
- durable append-only audit storage
- C6 SaaS Core authenticated tenant integration
- C6 SaaS Core now has canonical persisted audit events, runtime intent authorization, persistent kill-switch state, and human-override audit emission; deployment migration, authenticated runtime proof, and product-wide enforcement remain GAP
- production golden-set execution and feedback loop
- production active-memory graph/storage/retrieval wiring
- live AI Register ingestion from the agent estate
- formal Board reporting workflow
- C6, Ubernie and RemotePay repository liaisons wired to Holding
- external legal/regulatory compliance certification

No third-party Akeyless/Saviynt dependency has been introduced.

## Latest platform wiring

C6 SaaS Core now exposes `/api/v1/audit` plus `/api/v1/runtime/authorize`, `/api/v1/runtime/kill-switch`, and `/api/v1/runtime/human-override`. Runtime mutations require the `CONTROL_PLANE_KEY`/`X-C6-Control-Key` control-plane credential and write audit events. Migrations `002_create_audit_events.sql` and `003_create_kill_switches.sql` establish persistence contracts. This is not yet evidence of deployed runtime enforcement across the product estate.

## Critical governance boundary

The controls in this repository are engineering/governance mechanisms. They do not by themselves establish compliance with King IV/V, the Companies Act, POPIA, FIC Act, or any other law. Those mappings require current authoritative sources and, where appropriate, professional legal review.
