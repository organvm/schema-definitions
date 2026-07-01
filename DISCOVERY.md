# DISCOVERY - organvm/schema-definitions

**Verdict:** VALUE FOUND -> promote into the ranked tier.
**Date:** 2026-07-01 (auto-discovery)

## Value Thesis

`organvm/schema-definitions` is the estate's **contract spine**: not a standalone end-user product yet, but the reusable assurance layer that lets the rest of ORGANVM route, validate, publish, and govern without relying on tribal file-shape conventions. The repo already contains 34 Draft 2020-12 JSON Schemas, 29 JSON/YAML examples, an installable Python package exposing the `organvm-validate` CLI, 56 schema tests, and CI across Python 3.11/3.12 for registry, seed, governance, dispatch, soak, system metrics, ecosystem, organism, pulse, UAKS, corpus-surface, storefront, and ontology payloads. Its highest latent value is an **AI-organization contract kit**: every organ, dashboard, dispatcher, corpus pipeline, and storefront generator can depend on one versioned package to reject malformed state before it poisons routing, metrics, or product surfaces. Promote it because the contracts and gates already exist; the missing build-out is adoption packaging, not invention. The single best concrete first task is to ship a generated `schemas/catalog.json` plus a reusable `organvm-validate-repo` CLI/GitHub Action that validates `seed.yaml`, `ecosystem.yaml`, `network-map.yaml`, and known ORGANVM artifacts in any repo, then pilot that gate in `organvm-engine` and `system-dashboard`.

## What It Already Does

- Defines canonical JSON Schema contracts under `schemas/`, including `registry-v2`, `seed-v1`, `seed-v1.1`, `governance-rules`, `dispatch-payload`, `pulse-event`, `ecosystem-v1`, `system-organism`, corpus surface bundles, and UAKS atom contracts.
- Provides matching examples under `examples/` for human and automated conformance checks.
- Exposes `scripts/validate.py` as the `organvm-validate` console script, with filename-based schema detection and `--all-examples` validation.
- Runs CI with ruff, pyright, pytest, and full example validation.

## Single Best Concrete First Task

Ship a generated schema catalog and reusable repo validation gate: add `schemas/catalog.json` generated from every schema `$id`/title/description/example mapping, add an `organvm-validate-repo` mode that discovers standard ORGANVM files in a downstream checkout, and publish an `action.yml` so every repo can add the contract gate without copying validation glue.
