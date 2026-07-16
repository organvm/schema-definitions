#!/usr/bin/env python3
"""Validate governance-memory contracts and their cross-field invariants.

JSON Schema handles the portable shape of each contract. This validator owns
the invariants that require comparing multiple records, such as a coverage
denominator matching its source set or a verified external assertion carrying
two independent evidence groups.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"

CONTRACT_TO_SCHEMA = {
    "owner-reference.v1": "owner-reference.v1.schema.json",
    "parameter-contract.v1": "parameter-contract.v1.schema.json",
    "source-envelope.v1": "source-envelope.v1.schema.json",
    "assertion-evidence.v1": "assertion-evidence.v1.schema.json",
    "lineage-graph.v1": "lineage-graph.v1.schema.json",
    "governance-testament.v1": "governance-testament.v1.schema.json",
    "node-self-image.v1": "node-self-image.v1.schema.json",
    "coverage-receipt.v1": "coverage-receipt.v1.schema.json",
}

SOURCE_STATUSES = (
    "acquired",
    "parsed",
    "quarantined",
    "inaccessible",
    "missing_expected",
    "owner_blocked",
)


def load_json(path: Path) -> Any:
    """Load one JSON document."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _coverage_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = data.get("sources")
    denominator = data.get("denominator")
    counts = data.get("counts")
    residuals = data.get("residual_owners")
    if not isinstance(sources, list):
        return errors

    source_ids = [item.get("source_id") for item in sources if isinstance(item, dict)]
    duplicate_ids = sorted(
        source_id
        for source_id, count in Counter(source_ids).items()
        if source_id is not None and count > 1
    )
    if duplicate_ids:
        errors.append(f"sources contain duplicate source_id values: {duplicate_ids}")

    if isinstance(denominator, dict) and denominator.get("count") != len(sources):
        errors.append(
            "denominator.count must equal the number of classified source records"
        )

    expected_counts = Counter(
        item.get("status") for item in sources if isinstance(item, dict)
    )
    if isinstance(counts, dict):
        for status in SOURCE_STATUSES:
            if counts.get(status) != expected_counts.get(status, 0):
                errors.append(
                    f"counts.{status} must equal the number of sources with status {status!r}"
                )

    expected_residuals = {
        item.get("source_id"): {
            "owner_reference": item.get("owner_reference"),
            "failed_predicate": item.get("failed_predicate"),
            "next_action": item.get("next_action"),
        }
        for item in sources
        if isinstance(item, dict) and item.get("status") != "parsed"
    }
    actual_residuals: dict[Any, dict[str, Any]] = {}
    if isinstance(residuals, list):
        for residual in residuals:
            if not isinstance(residual, dict):
                continue
            source_id = residual.get("source_id")
            if source_id in actual_residuals:
                errors.append(
                    f"residual_owners contains duplicate source_id {source_id!r}"
                )
            actual_residuals[source_id] = {
                "owner_reference": residual.get("owner_reference"),
                "failed_predicate": residual.get("failed_predicate"),
                "next_action": residual.get("next_action"),
            }
        if actual_residuals != expected_residuals:
            errors.append(
                "residual_owners must exactly mirror every non-parsed source and its owner action"
            )

    expected_exact_all = (
        len(source_ids) == len(set(source_ids))
        and isinstance(denominator, dict)
        and denominator.get("count") == len(sources)
        and all(
            isinstance(source, dict) and source.get("status") == "parsed"
            for source in sources
        )
        and actual_residuals == expected_residuals
    )
    if data.get("exact_all") is not expected_exact_all:
        errors.append(
            "exact_all must be true exactly when each unique discovered source is parsed"
        )

    return errors


def _assertion_errors(data: dict[str, Any]) -> list[str]:
    if data.get("verification_state") != "verified":
        return []

    errors: list[str] = []
    evidence = data.get("evidence_references")
    if not isinstance(evidence, list):
        return errors
    groups = {
        item.get("independence_group")
        for item in evidence
        if isinstance(item, dict) and item.get("independence_group")
    }
    evidence_types = {
        item.get("evidence_type") for item in evidence if isinstance(item, dict)
    }
    assertion_class = data.get("assertion_class")

    if assertion_class == "external_fact" and len(groups) < 2:
        errors.append(
            "a verified external_fact requires at least two independent evidence groups"
        )
    if assertion_class == "operator_directive":
        required = {"immutable_source_event", "ratified_constitutional_record"}
        missing = sorted(required - evidence_types)
        if missing:
            errors.append(
                "a verified operator_directive is missing evidence types: "
                + ", ".join(missing)
            )
    if assertion_class == "current_state":
        required = {"owner_record", "fresh_verifier_receipt"}
        missing = sorted(required - evidence_types)
        if missing:
            errors.append(
                "a verified current_state is missing evidence types: "
                + ", ".join(missing)
            )
        freshness = data.get("freshness")
        if not isinstance(freshness, dict) or freshness.get("status") != "fresh":
            errors.append("a verified current_state requires freshness.status 'fresh'")

    return errors


def _parameter_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    parameters = data.get("parameters")
    if not isinstance(parameters, list):
        return errors

    for index, parameter in enumerate(parameters):
        if not isinstance(parameter, dict):
            continue
        key = parameter.get("key", f"index {index}")
        is_secret = (
            parameter.get("value_type") == "secret_reference"
            or parameter.get("secret_reference_policy") in {"reference_only", "required"}
        )
        if not is_secret:
            continue
        forbidden_fields = sorted(
            field
            for field in ("default", "resolved_value", "example_value")
            if field in parameter
        )
        if forbidden_fields:
            errors.append(
                f"secret parameter {key!r} contains committed value fields: "
                + ", ".join(forbidden_fields)
            )
        resolver = parameter.get("resolver")
        if isinstance(resolver, dict) and resolver.get("source") not in {
            "environment",
            "secret_store",
        }:
            errors.append(
                f"secret parameter {key!r} must resolve through environment or secret_store"
            )

    return errors


def _lineage_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    nodes = data.get("nodes")
    edges = data.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return errors

    node_ids = [node.get("node_id") for node in nodes if isinstance(node, dict)]
    duplicate_nodes = sorted(
        node_id
        for node_id, count in Counter(node_ids).items()
        if node_id is not None and count > 1
    )
    if duplicate_nodes:
        errors.append(f"nodes contain duplicate node_id values: {duplicate_nodes}")
    nodes_by_id = {
        node.get("node_id"): node for node in nodes if isinstance(node, dict)
    }

    edge_ids = [edge.get("edge_id") for edge in edges if isinstance(edge, dict)]
    duplicate_edges = sorted(
        edge_id
        for edge_id, count in Counter(edge_ids).items()
        if edge_id is not None and count > 1
    )
    if duplicate_edges:
        errors.append(f"edges contain duplicate edge_id values: {duplicate_edges}")

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        edge_id = edge.get("edge_id", "<unknown>")
        source_node = nodes_by_id.get(edge.get("from_node"))
        target_node = nodes_by_id.get(edge.get("to_node"))
        if source_node is None:
            errors.append(f"edge {edge_id!r} references an unknown from_node")
        if target_node is None:
            errors.append(f"edge {edge_id!r} references an unknown to_node")
        if edge.get("edge_type") == "adopts":
            if edge.get("review_state") != "reviewed" or not edge.get(
                "reviewer_reference"
            ):
                errors.append(
                    f"adoption edge {edge_id!r} requires reviewed state and a reviewer"
                )
            if source_node and target_node and not (
                source_node.get("lane") == "artifact"
                and target_node.get("lane") == "operator_intent"
            ):
                errors.append(
                    f"adoption edge {edge_id!r} must run from artifact to operator intent"
                )

    return errors


def semantic_errors(data: Any) -> list[str]:
    """Return contract-specific semantic invariant failures."""
    if not isinstance(data, dict):
        return []
    contract_name = data.get("contract_name")
    if contract_name == "coverage-receipt.v1":
        return _coverage_errors(data)
    if contract_name == "assertion-evidence.v1":
        return _assertion_errors(data)
    if contract_name == "parameter-contract.v1":
        return _parameter_errors(data)
    if contract_name == "lineage-graph.v1":
        return _lineage_errors(data)
    return []


def validate_document(
    data: Any, schemas_dir: Path = SCHEMAS_DIR
) -> tuple[list[str], list[str]]:
    """Return (schema errors, semantic errors) for one decoded document."""
    contract_name = data.get("contract_name") if isinstance(data, dict) else None
    schema_filename = CONTRACT_TO_SCHEMA.get(contract_name)
    if schema_filename is None:
        return [f"unknown governance-memory contract_name: {contract_name!r}"], []
    schema = load_json(schemas_dir / schema_filename)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = []
    for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        path = ".".join(str(part) for part in error.absolute_path) or "(root)"
        schema_errors.append(f"{path}: {error.message}")
    return schema_errors, semantic_errors(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate governance-memory contracts and semantic invariants"
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--schemas-dir", type=Path, default=SCHEMAS_DIR)
    args = parser.parse_args()

    failures = 0
    for path in args.files:
        try:
            data = load_json(path)
            schema_errors, invariant_errors = validate_document(data, args.schemas_dir)
        except (OSError, json.JSONDecodeError) as exc:
            schema_errors, invariant_errors = [str(exc)], []
        errors = [*(f"schema: {error}" for error in schema_errors), *(
            f"semantic: {error}" for error in invariant_errors
        )]
        if errors:
            failures += 1
            print(f"FAIL {path}")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"PASS {path}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
