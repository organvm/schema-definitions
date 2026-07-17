"""Regression tests for the governance-memory public contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import rfc8785
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
    "source-census.v1": "source-census-v1-example.json",
    "normalized-event.v1": "normalized-event-v1-example.json",
    "normalization-parity-receipt.v1": "normalization-parity-receipt-v1-example.json",
    "ideal-form-register.v1": "ideal-form-register-v1-example.json",
    "iceberg-atlas.v1": "iceberg-atlas-v1-example.json",
    "node-self-image-set.v1": "node-self-image-set-v1-example.json",
    "governance-stage-receipt.v1": "governance-stage-receipt-v1-example.json",
    "governance-cadence-receipt.v1": "governance-cadence-receipt-v1-example.json",
    "governance-atlas-receipt.v1": "governance-atlas-receipt-v1-example.json",
    "governance-snapshot-bundle.v1": "governance-snapshot-bundle-v1-example.json",
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
    data["unresolved_blockers"] = []
    data["closure_status"] = "ready"
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


def test_stable_event_identity_excludes_snapshot_order_and_provider_display_data():
    baseline = load(EXAMPLES_DIR / "normalized-event-v1-example.json")
    event_id = baseline["event_id"]
    candidates = []

    changed_snapshot = copy.deepcopy(baseline)
    changed_snapshot["snapshot_id"] = "snapshot-reordered-fixture"
    candidates.append(changed_snapshot)

    changed_transport = copy.deepcopy(baseline)
    changed_transport["transport_metadata"] = {
        "line_number": 999,
        "source_order": 100,
        "provider_order": 1,
        "transport_position": "fork",
    }
    candidates.append(changed_transport)

    renamed_provider = copy.deepcopy(baseline)
    renamed_provider["source_family"] = "provider-display-name-after-rename"
    candidates.append(renamed_provider)

    for candidate in candidates:
        assert candidate["event_id"] == event_id
        schema_errors, invariant_errors = validate_document(candidate)
        assert schema_errors == []
        assert invariant_errors == []


def test_event_identity_basis_prohibits_snapshot_and_transport_position_fields():
    baseline = load(EXAMPLES_DIR / "normalized-event-v1-example.json")
    for forbidden_field, value in (
        ("snapshot_id", "snapshot-forbidden"),
        ("line_number", 17),
        ("source_order", 2),
        ("provider_order", 3),
        ("transport_position", "fork"),
    ):
        candidate = copy.deepcopy(baseline)
        candidate["identity_basis"][forbidden_field] = value
        schema_errors, _ = validate_document(candidate)
        assert schema_errors, forbidden_field


def test_event_id_is_recomputed_from_native_identity_role_and_content():
    data = load(EXAMPLES_DIR / "normalized-event-v1-example.json")
    data["identity_basis"]["native_identifiers"]["event_id"] = "different-native-event"
    schema_errors, invariant_errors = validate_document(data)
    assert schema_errors == []
    assert any("event_id must equal" in error for error in invariant_errors)


def test_event_identity_uses_rfc8785_unicode_key_order() -> None:
    data = load(EXAMPLES_DIR / "normalized-event-v1-example.json")
    identifiers = data["identity_basis"]["native_identifiers"]
    identifiers["\U0001f600"] = "supplementary-plane-key"
    identifiers["\ue000"] = "private-use-key"
    data["event_id"] = "evt_" + hashlib.sha256(
        rfc8785.dumps(data["identity_basis"])
    ).hexdigest()

    schema_errors, invariant_errors = validate_document(data)

    assert schema_errors == []
    assert invariant_errors == []


def test_normalization_parity_requires_every_census_unit_exactly_once():
    baseline = load(
        EXAMPLES_DIR / "normalization-parity-receipt-v1-example.json"
    )

    missing = copy.deepcopy(baseline)
    missing["promotions"].pop()
    assert semantic_errors(missing)

    duplicate = copy.deepcopy(baseline)
    duplicate["promotions"].append(copy.deepcopy(duplicate["promotions"][0]))
    assert semantic_errors(duplicate)

    extra = copy.deepcopy(baseline)
    extra["promotions"].append(
        {
            "raw_unit_id": "raw_not_in_census",
            "disposition": {
                "type": "ignored_transport_echo",
                "owner_reference": "owner_normalizer",
                "failed_predicate": "transport echo creates no authority event",
                "next_action": "Retain the reviewed echo disposition.",
                "evidence_references": ["receipt:echo-review"],
            },
        }
    )
    assert semantic_errors(extra)


def test_parity_owner_routed_debt_can_be_exact_but_never_ready():
    data = load(EXAMPLES_DIR / "normalization-parity-receipt-v1-example.json")
    assert data["readiness"]["exact_all"] is True
    assert data["readiness"]["ready"] is False
    assert semantic_errors(data) == []

    data["readiness"]["ready"] = True
    data["readiness"]["status"] = "ready"
    assert semantic_errors(data)


def test_ready_rejects_every_truth_first_debt_class():
    baseline = load(EXAMPLES_DIR / "governance-atlas-receipt-v1-example.json")
    for debt_field in (
        "unresolved_blockers",
        "quarantines",
        "missing_requirements",
        "citation_debt",
        "incomplete_predicates",
    ):
        candidate = copy.deepcopy(baseline)
        candidate["readiness"][debt_field] = [f"debt:{debt_field}"]
        assert semantic_errors(candidate), debt_field


def test_ideal_state_and_distance_are_recomputed_from_receipt_results():
    data = load(EXAMPLES_DIR / "ideal-form-register-v1-example.json")
    ideal = data["ideal_forms"][0]
    ideal["implementation_state"] = "partial"
    ideal["distance_to_ideal"]["classification"] = "partial"
    assert semantic_errors(data)


def test_self_image_set_requires_exactly_one_image_per_registered_node():
    data = load(EXAMPLES_DIR / "node-self-image-set-v1-example.json")
    data["registered_node_ids"].append("ent_repo_missing_self_image")
    data["counts"]["registered"] = 2
    assert semantic_errors(data)


def test_stage_receipt_enforces_output_and_child_bounds():
    data = load(EXAMPLES_DIR / "governance-stage-receipt-v1-example.json")
    data["outputs"][0]["size_bytes"] = data["execution_limits"]["max_output_bytes"] + 1
    assert semantic_errors(data)


def test_cadence_receipt_requires_exact_predecessor_hash_chain():
    data = load(EXAMPLES_DIR / "governance-cadence-receipt-v1-example.json")
    data["stage_receipts"][4]["predecessor_receipt_digest"] = (
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    assert semantic_errors(data)


def test_snapshot_bundle_ready_requires_two_runs_and_post_proof_fixed_point():
    data = load(EXAMPLES_DIR / "governance-snapshot-bundle-v1-example.json")
    data["governance_cadence_receipts"].pop()
    assert semantic_errors(data)

    data = load(EXAMPLES_DIR / "governance-snapshot-bundle-v1-example.json")
    data["post_proof_idempotence"]["emitted_receipt_count"] = 1
    schema_errors, _ = validate_document(data)
    assert schema_errors


def test_snapshot_bundle_recursively_validates_embedded_events():
    data = load(EXAMPLES_DIR / "governance-snapshot-bundle-v1-example.json")
    data["normalized_events"][0]["event_id"] = "evt_" + "0" * 64
    assert semantic_errors(data)


def test_candidate_testament_cannot_carry_ratification():
    data = load(EXAMPLES_DIR / "governance-testament-v1-example.json")
    data["status"] = "candidate"
    schema_errors, _ = validate_document(data)
    assert schema_errors


def test_ratified_testament_fails_when_constitutional_scope_is_blocked():
    data = load(EXAMPLES_DIR / "governance-testament-v1-example.json")
    coverage = data["ratification"]["constitutional_coverage"]
    coverage["blocked_scopes"] = ["scope:operator-authority"]
    coverage["ready"] = False
    schema_errors, invariant_errors = validate_document(data)
    assert schema_errors == []
    assert any("ratified status is impossible" in error for error in invariant_errors)


def test_empty_strict_governance_content_is_rejected():
    census = load(EXAMPLES_DIR / "source-census-v1-example.json")
    census["raw_units"] = []
    assert validate_document(census)[0]

    assertion = load(EXAMPLES_DIR / "assertion-evidence-v1-example.json")
    assertion["evidence_references"] = []
    assert validate_document(assertion)[0]

    lineage = load(EXAMPLES_DIR / "lineage-graph-v1-example.json")
    lineage["nodes"] = []
    assert validate_document(lineage)[0]

    testament = load(EXAMPLES_DIR / "governance-testament-v1-example.json")
    testament["directive"] = ""
    assert validate_document(testament)[0]

    atlas = load(EXAMPLES_DIR / "iceberg-atlas-v1-example.json")
    atlas["timelines"]["operator_intent"] = []
    assert validate_document(atlas)[0]

    atlas = load(EXAMPLES_DIR / "iceberg-atlas-v1-example.json")
    atlas["relationships"] = []
    assert validate_document(atlas)[0]

    ideals = load(EXAMPLES_DIR / "ideal-form-register-v1-example.json")
    ideals["ideal_forms"] = []
    assert validate_document(ideals)[0]

    self_images = load(EXAMPLES_DIR / "node-self-image-set-v1-example.json")
    self_images["self_images"] = []
    assert validate_document(self_images)[0]

    stage = load(EXAMPLES_DIR / "governance-stage-receipt-v1-example.json")
    stage["child_receipts"] = []
    assert validate_document(stage)[0]

    bundle = load(EXAMPLES_DIR / "governance-snapshot-bundle-v1-example.json")
    bundle["source_envelopes"] = []
    assert validate_document(bundle)[0]
