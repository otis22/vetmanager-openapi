#!/usr/bin/env python3
"""Local and CI validation for the committed Vetmanager OpenAPI artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}
SECRET_PATTERNS = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(?:\+7[\s(.-]*|8[\s(-]+)\d{3}[\s).:-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}\b"),
    re.compile(r"\(\d{3}\)\s*\d{3}-\d{2}-\d{2}"),
    re.compile(r"\b[0-9a-f]{32}\b", re.I),
    re.compile(r"X-REST-API-KEY\s*[:=]\s*[^,\s)]+", re.I),
]
ALLOWED_PLACEHOLDER_TOKENS = {
    "00000000000000000000000000000000",
    "user@example.test",
    "+7 (000) 000-00-00",
    "(000) 000-00-00",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_structure(spec: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(spec.get("openapi"), str) or not spec["openapi"].startswith("3.0."):
        fail(errors, "openapi must be 3.0.x")
    if not isinstance(spec.get("info"), dict) or not spec["info"].get("title"):
        fail(errors, "info.title is required")
    if not isinstance(spec.get("paths"), dict) or not spec["paths"]:
        fail(errors, "paths must be a non-empty object")

    operation_ids: set[str] = set()
    for path, path_item in spec.get("paths", {}).items():
        if not path.startswith("/"):
            fail(errors, f"path must start with /: {path}")
        if re.search(r"/\d+(?:/|$)", path):
            fail(errors, f"path contains literal numeric example segment: {path}")
        if path != "/" and path.endswith("/"):
            fail(errors, f"path must not end with trailing slash: {path}")
        if not isinstance(path_item, dict):
            fail(errors, f"path item must be an object: {path}")
            continue

        path_params = set(re.findall(r"\{([^}]+)\}", path))
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                fail(errors, f"operation must be an object: {method.upper()} {path}")
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                fail(errors, f"operationId is required: {method.upper()} {path}")
            elif operation_id in operation_ids:
                fail(errors, f"duplicate operationId: {operation_id}")
            else:
                operation_ids.add(operation_id)

            declared_path_params = {
                p.get("name")
                for p in operation.get("parameters", [])
                if isinstance(p, dict) and p.get("in") == "path"
            }
            for param_name in path_params:
                if param_name not in declared_path_params:
                    fail(errors, f"missing path parameter {param_name}: {method.upper()} {path}")
            for param in operation.get("parameters", []):
                if isinstance(param, dict) and param.get("in") == "path" and param.get("required") is not True:
                    fail(errors, f"path parameter must be required: {method.upper()} {path} {param.get('name')}")


def validate_swagger_ui(root: Path, errors: list[str]) -> None:
    index = root / "index.html"
    initializer = root / "dist" / "swagger-initializer.js"
    spec = root / "vetmanager_openapi_v6.yaml"
    for path in (index, initializer, spec):
        if not path.exists():
            fail(errors, f"required Swagger UI file is missing: {path.relative_to(root)}")
    if initializer.exists():
        text = initializer.read_text(encoding="utf-8", errors="ignore")
        if 'url: "vetmanager_openapi_v6.yaml"' not in text:
            fail(errors, "dist/swagger-initializer.js must reference vetmanager_openapi_v6.yaml")
    if index.exists():
        text = index.read_text(encoding="utf-8", errors="ignore")
        for asset in ("dist/swagger-ui.css", "dist/swagger-ui-bundle.js", "dist/swagger-ui-standalone-preset.js", "dist/swagger-initializer.js"):
            if asset not in text:
                fail(errors, f"index.html does not reference {asset}")


def validate_no_secrets(root: Path, errors: list[str]) -> None:
    checked_roots = [
        root / "README.md",
        root / "scripts",
        root / "artifacts" / "reconciliation",
        root / "vetmanager_openapi_v6.json",
        root / "vetmanager_openapi_v6.yaml",
    ]
    for checked in checked_roots:
        paths = [checked] if checked.is_file() else list(checked.rglob("*")) if checked.exists() else []
        for path in paths:
            if not path.is_file():
                continue
            if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_PATTERNS:
                for match in pattern.finditer(text):
                    token = match.group(0)
                    if token in ALLOWED_PLACEHOLDER_TOKENS:
                        continue
                    fail(errors, f"possible secret literal in {path.relative_to(root)}")
                    break


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skip-secret-scan", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    json_path = root / "vetmanager_openapi_v6.json"
    yaml_path = root / "vetmanager_openapi_v6.yaml"
    errors: list[str] = []

    json_spec = load_json(json_path)
    yaml_spec = load_yaml(yaml_path)
    if json_spec != yaml_spec:
        fail(errors, "vetmanager_openapi_v6.json and vetmanager_openapi_v6.yaml are not equivalent")

    validate_structure(json_spec, errors)
    validate_swagger_ui(root, errors)
    if not args.skip_secret_scan:
        validate_no_secrets(root, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    operation_count = sum(
        1
        for path_item in json_spec.get("paths", {}).values()
        for method in path_item
        if method in HTTP_METHODS
    )
    print(
        json.dumps(
            {
                "valid": True,
                "paths": len(json_spec.get("paths", {})),
                "operations": operation_count,
                "schemas": len(json_spec.get("components", {}).get("schemas", {})),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
