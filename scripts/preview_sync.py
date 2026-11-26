#!/usr/bin/env python3
"""Preview OpenAPI reconciliation against a committed vetmanager-extjs revision."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from difflib import unified_diff
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

import reconcile_openapi as reconcile
from api_contract_checks import run_http_checks
from validate_openapi import validate_structure


REST_ROOT = "rest/protected"
ROUTE_FILES = (f"{REST_ROOT}/config/main.php", f"{REST_ROOT}/controllers")
REVIEW_PATHS = (
    *ROUTE_FILES,
    f"{REST_ROOT}/config/main.template.php",
    f"{REST_ROOT}/components",
    f"{REST_ROOT}/models",
    f"{REST_ROOT}/extensions/restfullyii/components",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def collect_routes(repo: Path, commit: str, snapshot: Path, documented_keys: set[str]) -> dict:
    with tempfile.TemporaryFile() as archive:
        subprocess.run(
            ["git", "-C", str(repo), "archive", commit, *ROUTE_FILES],
            stdout=archive,
            check=True,
        )
        archive.seek(0)
        with tarfile.open(fileobj=archive) as files:
            files.extractall(snapshot, filter="data")

    reconcile.EXTJS_MAIN = snapshot / ROUTE_FILES[0]
    reconcile.EXTJS_CONTROLLERS = snapshot / ROUTE_FILES[1]
    routes = reconcile.collect_extjs_routes(documented_keys)
    if not routes:
        raise ValueError(f"No REST routes found in backend commit {commit}")
    return routes


def contract_lines(spec: dict) -> list[str]:
    contract = deepcopy(spec)
    contract.pop("x-reconciliation", None)
    for item in contract["paths"].values():
        for method, operation in item.items():
            if method.lower() in reconcile.HTTP_METHODS and isinstance(operation, dict):
                operation.pop("x-reconciliation", None)
    return (json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n").splitlines(keepends=True)


def spec_diff(before: dict, after: dict) -> str:
    return "".join(unified_diff(
        contract_lines(before),
        contract_lines(after),
        fromfile=f"a/{reconcile.OPENAPI_JSON.name}",
        tofile=f"b/{reconcile.OPENAPI_JSON.name}",
    ))


def review_report(
    revision: str, selected: str, baseline: str, base: str, openapi_commit: str,
    files: list[str], rows: list[dict], previous: dict, current: dict,
) -> str:
    changed_controllers = {
        Path(path).name for path in files if path.startswith(f"{REST_ROOT}/controllers/")
    }
    affected = [
        row["key"] for row in rows
        if row["openapi"] and row.get("extjs_controller") in changed_controllers
    ]
    undocumented = [row["key"] for row in rows if row["status"] == "extjs_only_candidate"]
    unmatched = [row["key"] for row in rows if row["status"] == "openapi_only"]
    counts = Counter(row["status"] for row in rows)
    lines = [
        "# Предпросмотр синхронизации OpenAPI",
        "",
        f"- Бэкенд {revision} — `{selected}`",
        f"- База сравнения {baseline} — общий коммит `{base}`",
        f"- Спецификация из рабочей копии OpenAPI на базе `{openapi_commit}`",
        "",
        "Diff показывает изменения спецификации без служебных метаданных сверки. Отчёт показывает, где нужно проверить контракт по коду и HTTP.",
        "Изменённый контроллер может повлиять на несколько операций. Совпадение маршрута не подтверждает структуру запроса или ответа.",
        "",
        "## Итоги сверки",
        "",
        *[f"- `{status}` — {count}" for status, count in sorted(counts.items())],
    ]
    sections = [
        ("Новые маршруты относительно базы", sorted(current.keys() - previous.keys())),
        ("Маршруты, исчезнувшие относительно базы", sorted(previous.keys() - current.keys())),
        ("Изменённые REST-файлы", files),
        ("Описанные операции в изменённых контроллерах", affected),
        ("Кандидаты на добавление в OpenAPI", undocumented),
        ("Описанные операции без совпадения в сборщике", unmatched),
    ]
    for title, items in sections:
        lines.extend(["", f"## {title} ({len(items)})", ""])
        lines.extend((f"- `{item}`" for item in items) if items else ["Нет."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Backend branch, tag or commit. Use HEAD for the current branch.")
    parser.add_argument("--compare-to", default="origin/master", help="Backend reference for the review report")
    parser.add_argument("--extjs-root", type=Path, default=reconcile.EXTJS_ROOT, help="Local backend checkout")
    parser.add_argument("--output", type=Path, help="New output directory. Defaults to a temporary directory.")
    parser.add_argument("--api-base-url", help="Test stand URL for optional HTTP checks")
    args = parser.parse_args()

    try:
        if args.output is not None and (args.output.exists() or args.output.is_symlink()):
            raise ValueError(f"Output already exists: {args.output}")
        backend = args.extjs_root.resolve()
        selected = git(backend, "rev-parse", "--verify", "--end-of-options", f"{args.revision}^{{commit}}")
        target = git(backend, "rev-parse", "--verify", "--end-of-options", f"{args.compare_to}^{{commit}}")
        base = git(backend, "merge-base", target, selected)
        openapi_commit = git(reconcile.ROOT, "rev-parse", "HEAD")

        if reconcile.yaml is None:
            raise ValueError("PyYAML is required. Install it with python3 -m pip install pyyaml.")
        spec = reconcile.read_json(reconcile.OPENAPI_JSON)
        yaml_spec = reconcile.yaml.safe_load(reconcile.OPENAPI_YAML.read_text(encoding="utf-8-sig"))
        if spec != yaml_spec:
            raise ValueError("The working OpenAPI JSON and YAML files differ")
        documented = reconcile.collect_openapi(spec, "openapi")
        excluded = reconcile.load_excluded_routes(reconcile.EXCLUDED_ROUTES_FILE)

        with tempfile.TemporaryDirectory(prefix="vetmanager-rest-snapshot-") as name:
            work = Path(name)
            current = collect_routes(backend, selected, work / "selected", set(documented))
            previous = current if base == selected else collect_routes(backend, base, work / "base", set(documented))

        rows = reconcile.merge_endpoint_sources(("openapi", documented), ("extjs", current), excluded_routes=excluded)
        proposed = reconcile.apply_reconciliation_to_spec(spec, rows, {})
        proposed["info"] = spec["info"]
        errors: list[str] = []
        validate_structure(proposed, errors)
        if errors:
            raise ValueError("\n".join(errors))

        files = git(backend, "diff", "--name-only", "--no-renames", base, selected, "--", *REVIEW_PATHS).splitlines()
        report = review_report(
            args.revision, selected, args.compare_to, base, openapi_commit, files, rows, previous, current,
        )
        diff = spec_diff(spec, proposed)
        output = args.output if args.output is not None else Path(tempfile.mkdtemp(prefix="vetmanager-openapi-preview-"))
        if args.output is not None:
            output.mkdir()
        (output / "openapi.diff").write_text(diff, encoding="utf-8")
        (output / "review.md").write_text(report, encoding="utf-8")
        candidates = [
            {"method": row["method"], "path": row["path"], "source": row["extjs_source"],
             "controller": row.get("extjs_controller"), "action": row.get("extjs_method_name")}
            for row in rows if row["status"] == "extjs_only_candidate"
            and "{controller}" not in row["path"]
        ]
        reconcile.write_json(output / "route-candidates.json", candidates)
        http_failures = 0
        if args.api_base_url:
            http_report, http_failures = run_http_checks(proposed, args.api_base_url)
            (output / "http-checks.md").write_text(http_report, encoding="utf-8")
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, tarfile.TarError) as exc:
        print(f"OpenAPI preview failed: {exc}", file=sys.stderr)
        return 1

    print(f"Backend commit: {selected}")
    print(f"Spec diff: {output / 'openapi.diff'}" + ("" if diff else " (no changes)"))
    print(f"Review report: {output / 'review.md'}")
    if args.api_base_url:
        print(f"HTTP report: {output / 'http-checks.md'} ({http_failures} failures)")
    return int(http_failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
