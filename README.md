# schema-definitions

Canonical JSON Schema definitions for the organvm eight-organ system's data contracts.

## Schemas

| Schema | Validates | Source of Truth |
|--------|-----------|-----------------|
| `registry-v2.schema.json` | `registry-v2.json` | Repository state across all 8 organs |
| `seed-v1.schema.json` | `seed.yaml` | Per-repo automation contracts |
| `governance-rules.schema.json` | `governance-rules.json` | Dependency rules, promotion state machine |
| `dispatch-payload.schema.json` | Cross-org dispatch events | ORGAN-IV routing payloads |
| `soak-test.schema.json` | `daily-*.json` | VIGILIA soak test snapshots |
| `system-metrics.schema.json` | `system-metrics.json` | Computed + manual system metrics |
| `conversation-corpus-surface-manifest.schema.json` | `conversation-corpus-surface-manifest-*.json` | Exported CCE engine surface manifest |
| `conversation-corpus-mcp-context.schema.json` | `conversation-corpus-mcp-context-*.json` | Exported CCE MCP-facing context payload |
| `conversation-corpus-surface-bundle.schema.json` | `conversation-corpus-surface-bundle-*.json` | Exported CCE validation bundle |

### Governance-memory contracts

These versioned interfaces separate private source custody from public,
provider-neutral projections. Provider names, owner locations, repository URLs,
and other live values are contract data resolved at runtime; the schemas do not
embed a provider catalog or deployment-specific path.

| Contract | Responsibility |
|----------|----------------|
| `source-envelope.v1.schema.json` | Provider-neutral source identity, authority, raw-unit content binding, and private custody pointer |
| `lineage-graph.v1.schema.json` | Separate operator-intent and artifact timelines with reviewed typed edges |
| `governance-testament.v1.schema.json` | Ratified directives, layers, instruments, ideals, predicates, and citations |
| `assertion-evidence.v1.schema.json` | Evidence independence, verification, and freshness for assertions |
| `node-self-image.v1.schema.json` | Identity, relations, cursors, state, digests, and distance to active ideals |
| `coverage-receipt.v1.schema.json` | Dynamic denominator, exact classification, separate readiness, and residual owners |
| `owner-reference.v1.schema.json` | Stable owner IDs resolved through owner-native records |
| `parameter-contract.v1.schema.json` | Typed runtime parameters, validation, freshness, and secret-reference policy |
| `source-census.v1.schema.json` | Runtime enumeration of Git refs, workspaces, custody manifests, application stores, exports, and connectors |
| `normalized-event.v1.schema.json` | Stable native event identity plus immutable raw-unit content binding, independent of snapshot and transport position |
| `normalization-parity-receipt.v1.schema.json` | Complete content-bound raw-unit-to-event-or-disposition promotion crosswalk |
| `ideal-form-register.v1.schema.json` | Receipt-derived ideal status, implementation predicates, and distance |
| `iceberg-atlas.v1.schema.json` | Two authority timelines and six populated graph zooms |
| `node-self-image-set.v1.schema.json` | Exactly one valid self-image for every registered node |
| `governance-stage-receipt.v1.schema.json` | Bounded, resumable receipt for one cadence stage |
| `governance-cadence-receipt.v1.schema.json` | Ordered nine-stage receipt chain and fixed-point evidence |
| `governance-atlas-receipt.v1.schema.json` | Assertion, ideal, self-image, timeline, zoom, and Atlas readiness |
| `governance-snapshot-bundle.v1.schema.json` | Frozen cross-owner bundle with two-run and post-proof idempotence |

`exact_all` means complete classification of the declared denominator. It does
not mean ready. Wherever a contract exposes `readiness`, `ready` additionally
requires no unresolved blockers, quarantines, missing requirements, citation
debt, or incomplete predicates. `closed_with_owner_routed_debt` is an honest
closure state but can never alias `ready`.

The normalization contracts carry the census `raw_unit_content_hash` through
source envelopes, normalized events, and every parity promotion. The parity input
also embeds the full raw-unit/hash denominator, and semantic validation requires
the promotion bindings to match it exactly. Stable event IDs remain derived only
from native identity, native role, and normalized content identity.

## Usage

```bash
# Validate a file (auto-detects schema from filename)
python scripts/validate.py path/to/registry-v2.json

# Validate all examples
python scripts/validate.py --all-examples

# Validate governance-memory shape and cross-field invariants
python scripts/validate_governance_memory.py \
  examples/{owner-reference,parameter-contract,source-envelope,assertion-evidence,lineage-graph,governance-testament,node-self-image,coverage-receipt}-v1-example.json

# The same validator covers the truth-first census, normalization, Atlas,
# cadence, and frozen-bundle contracts listed above.

# Run tests
pytest
```

## Install

```bash
pip install -e ".[dev]"
```

Requires: Python 3.11+, `jsonschema`, `pyyaml`.

## Part of the Eight-Organ System

This repo belongs to **meta-organvm** (ORGAN VIII) and provides the data contracts that `organvm-engine` validates against.
