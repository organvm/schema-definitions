# Discovery: organvm/schema-definitions

## Value Thesis

`organvm/schema-definitions` has real ranked value as the ORGANVM estate's contract authority: it already publishes 34 JSON Schemas, example payloads, a Python validation CLI, and pytest coverage for registry state, seed contracts, governance rules, dispatch payloads, ecosystem profiles, Ontologia events, pulse/state snapshots, storefront metadata, UAKS atoms, and conversation-corpus surface exports. Its highest latent value is a reusable assurance and onboarding layer: every organ can use this repo to reject malformed state before dispatch, generate human-readable schema docs from one canonical source, and expose a machine-readable contract catalog to `organvm-engine`, dashboards, MCP surfaces, and future revenue/product packaging without each repo inventing its own validation rules.

## First Task

Generate a checked-in schema catalog and reference page from `schemas/*.json` plus `examples/*`, then add a `--check-catalog` validation gate so docs, examples, and CLI schema detection cannot drift from the canonical contract set.
