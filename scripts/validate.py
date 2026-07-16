#!/usr/bin/env python3
"""Validate JSON/YAML files against their corresponding JSON Schema.

Usage:
    python scripts/validate.py registry-v2.json
    python scripts/validate.py seed.yaml
    python scripts/validate.py --all-examples
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

# Map file name patterns to schemas
SCHEMA_MAP = {
    "owner-reference": "owner-reference.v1.schema.json",
    "parameter-contract": "parameter-contract.v1.schema.json",
    "source-envelope": "source-envelope.v1.schema.json",
    "assertion-evidence": "assertion-evidence.v1.schema.json",
    "lineage-graph": "lineage-graph.v1.schema.json",
    "governance-testament": "governance-testament.v1.schema.json",
    "node-self-image": "node-self-image.v1.schema.json",
    "coverage-receipt": "coverage-receipt.v1.schema.json",
    "ammoi": "ammoi-v1.schema.json",
    "evolution-policy": "evolution-policy.schema.json",
    "pulse-event": "pulse-event.schema.json",
    "sensing-signal": "sensing-signal.schema.json",
    "state-snapshot": "state-snapshot.schema.json",
    "testament-artifact": "testament-artifact.schema.json",
    "surface-manifest": "conversation-corpus-surface-manifest.schema.json",
    "mcp-context": "conversation-corpus-mcp-context.schema.json",
    "surface-bundle": "conversation-corpus-surface-bundle.schema.json",
    "system-organism": "system-organism.schema.json",
    "pillar-dna": "pillar-dna-v1.schema.json",
    "ecosystem": "ecosystem-v1.schema.json",
    "registry": "registry-v2.schema.json",
    "seed-v1.1": "seed-v1.1.schema.json",
    "seed": "seed-v1.schema.json",
    "governance": "governance-rules.schema.json",
    "dispatch": "dispatch-payload.schema.json",
    "soak": "soak-test.schema.json",
    "daily": "soak-test.schema.json",
    "metrics": "system-metrics.schema.json",
    "entity-identity": "entity-identity.schema.json",
    "name-record": "name-record.schema.json",
    "ontologia-event": "ontologia-event.schema.json",
    "organ-definitions": "organ-definitions.schema.json",
    "excavation-report": "excavation-report.schema.json",
    "workspace-manifest": "workspace-manifest-v1.schema.json",
    "uaks-assembly-recipe": "uaks-assembly-recipe.schema.json",
    "uaks-code-atom": "uaks-code-atom.schema.json",
    "uaks-source-object": "uaks-source-object.schema.json",
    "uaks-text-atom": "uaks-text-atom.schema.json",
    "uaks-validation-event": "uaks-validation-event.schema.json",
    "storefront": "storefront-v1.schema.json",
}


def detect_schema(filepath: Path) -> Path | None:
    """Auto-detect which schema to use based on filename."""
    name = filepath.stem.lower()
    for key, schema_file in SCHEMA_MAP.items():
        if key in name:
            return SCHEMAS_DIR / schema_file
    return None


def load_data(filepath: Path) -> dict:
    """Load JSON or YAML file."""
    suffix = filepath.suffix.lower()
    with open(filepath) as f:
        if suffix in (".yaml", ".yml"):
            if yaml is None:
                print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
                sys.exit(1)
            return yaml.safe_load(f)
        return json.load(f)


def validate_file(filepath: Path, schema_path: Path | None = None) -> tuple[bool, list[str]]:
    """Validate a file against a JSON Schema. Returns (pass, errors)."""
    if schema_path is None:
        schema_path = detect_schema(filepath)
    if schema_path is None:
        return False, [f"Cannot detect schema for {filepath.name}"]

    data = load_data(filepath)
    with open(schema_path) as f:
        schema = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

    messages = []
    for err in errors:
        path = ".".join(str(p) for p in err.absolute_path) or "(root)"
        messages.append(f"  {path}: {err.message}")

    return len(errors) == 0, messages


def main():
    parser = argparse.ArgumentParser(description="Validate files against JSON Schema")
    parser.add_argument("files", nargs="*", help="Files to validate")
    parser.add_argument("--schema", type=str, default=None,
                        help="Explicit schema file to use")
    parser.add_argument("--all-examples", action="store_true",
                        help="Validate all example files")
    args = parser.parse_args()

    targets = []
    if args.all_examples:
        targets.extend(sorted(EXAMPLES_DIR.glob("*.json")))
        targets.extend(sorted(EXAMPLES_DIR.glob("*.yaml")))
    targets.extend(Path(f) for f in args.files)

    if not targets:
        parser.print_help()
        return 0

    schema_override = Path(args.schema) if args.schema else None
    total_pass = 0
    total_fail = 0

    for filepath in targets:
        if not filepath.exists():
            print(f"SKIP {filepath}: not found")
            continue

        ok, errors = validate_file(filepath, schema_override)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {filepath.name}")

        if not ok:
            for err in errors:
                print(err)
            total_fail += 1
        else:
            total_pass += 1

    print(f"\n{total_pass} passed, {total_fail} failed")
    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
