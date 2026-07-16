# Changelog

## Unreleased

- Add eight governance-memory v1 contracts for source custody projections,
  dual-lane lineage, governance testament, assertion evidence, node self-images,
  exact coverage, owner resolution, and typed parameters.
- Add provider-neutral examples and semantic validation for exact coverage,
  evidence independence, reviewed adoption, and secret-reference safety.
- Add regression fixtures proving renamed and newly introduced providers require
  configuration changes only.

## 1.0.0 (2026-03-04)

- Formalized as v1.0.0 — all 6 schemas stable and validated in production since 2026-02-17
- `registry-v2.schema.json`: `schema_version` field now constrained to enum `["1.0.0", "1.0.1", "1.1.0"]`
- All schemas validated against live data across 103 repos for 15+ days
- No breaking changes from 0.1.0 — this release formalizes the existing contracts

## 0.1.0 (2026-02-17)

- Initial release: 6 JSON Schema definitions
- Schemas: registry-v2, seed-v1, governance-rules, dispatch-payload, soak-test, system-metrics
- Example files for registry, seed, and dispatch
- Validation script and pytest suite
