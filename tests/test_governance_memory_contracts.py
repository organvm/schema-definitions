"""Regression tests for the governance-memory public contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_governance_memory import (
    CONTRACT_TO_SCHEMA,
    semantic_errors,
    validate_document,
)


ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
EXAMPLES_DIR = ROOT / "examples"
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "governance-memory"

EXAMPLES = {
    "owner-reference.v1": "owner-reference-v1-example.json",
    "parameter-contract.v1": "parameter-contract-v1-example.json",
    "source-envelope.v1": "source-envelope-v1-example.json",
    "assertion-evidence.v1": "assertion-evidence-v1-example.json",
    "lineage-graph.v1": "lineage-graph-v1-example.json",
    "governance-testament.v1": "governance-testament-v1-example.json",
    "node-self-image.v1": "node-self-image-v1-example.json",
    "coverage-receipt.v1": "coverage-receipt-v1-example.json",
}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_all_governance_memory_schemas_are_valid_draft_202012():
    for schema_filename in CONTRACT_TO_SCHEMA.values():
        Draft202012Validator.check_schema(load(SCHEMAS_DIR / schema_filename))


def test_all_positive_examples_pass_schema_and_semantic_validation():
    for contract_name, example_filename in EXAMPLES.items():
        data = load(EXAMPLES_DIR / example_filename)
        assert data["contract_name"] == contract_name
        schema_errors, invariant_errors = validate_document(data)
        assert schema_errors == []
        assert invariant_errors == []


def test_provider_names_are_runtime_data_not_a_fixed_catalog():
    data = load(EXAMPLES_DIR / "source-envelope-v1-example.json")
    schema = load(SCHEMAS_DIR / "source-envelope.v1.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    for family, instance, adapter in (
        ("renamed-provider-2042", "desktop-rebrand", "adapter.rebrand.v9"),
        ("new-provider-never-seen", "account-001", "adapter.new.v1"),
    ):
        candidate = copy.deepcopy(data)
        candidate["source_family"] = family
        candidate["source_instance"] = instance
        candidate["format_adapter"] = adapter
        assert list(validator.iter_errors(candidate)) == []


def test_assistant_plan_is_rejected_from_operator_intent_lane():
    data = load(EXAMPLES_DIR / "lineage-graph-v1-example.json")
    schema = load(SCHEMAS_DIR / "lineage-graph.v1.schema.json")
    data["nodes"][1]["lane"] = "operator_intent"
    data["nodes"][1]["authority_class"] = "operator_intent"

    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data)
    )
    assert errors


def test_negative_semantic_fixtures_are_structurally_valid_but_rejected():
    fixtures = sorted(FIXTURES_DIR.glob("*.json"))
    assert fixtures
    for fixture in fixtures:
        data = load(fixture)
        schema_errors, invariant_errors = validate_document(data)
        assert schema_errors == [], fixture.name
        assert invariant_errors, fixture.name


def test_exact_coverage_can_retain_explicit_blocker_debt_without_being_ready():
    data = load(EXAMPLES_DIR / "coverage-receipt-v1-example.json")
    assert data["exact_all"] is True
    assert data["ready"] is False
    assert semantic_errors(data) == []


def test_all_parsed_coverage_is_exact_and_ready():
    data = load(EXAMPLES_DIR / "coverage-receipt-v1-example.json")
    data["sources"] = [data["sources"][0]]
    data["denominator"]["count"] = 1
    data["counts"]["owner_blocked"] = 0
    data["residual_owners"] = []
    data["ready"] = True
    assert semantic_errors(data) == []


def test_verified_operator_directive_requires_source_event_and_ratification():
    data = load(EXAMPLES_DIR / "assertion-evidence-v1-example.json")
    data["assertion_class"] = "operator_directive"
    assert semantic_errors(data)


def test_verified_current_state_requires_owner_fresh_verifier_and_freshness():
    data = load(EXAMPLES_DIR / "assertion-evidence-v1-example.json")
    data["assertion_class"] = "current_state"
    assert semantic_errors(data)
