#!/usr/bin/env python3
"""Reconcile Vetmanager OpenAPI against Postman, MCP, ExtJS and devtr6.

The script intentionally never writes raw Postman sync payloads or raw devtr6
responses. Artifacts contain endpoint metadata and compact response summaries.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path("/home/otis/myprojects/vetmanager-openapi")
MCP_ROOT = Path("/home/otis/myprojects/vetmanager-mcp")
EXTJS_ROOT = Path("/home/otis/myprojects/vetmanager-extjs")
ARTIFACTS = ROOT / "artifacts" / "reconciliation"

OPENAPI_JSON = ROOT / "vetmanager_openapi_v6.json"
OPENAPI_YAML = ROOT / "vetmanager_openapi_v6.yaml"
MCP_OPENAPI_JSON = MCP_ROOT / "artifacts" / "vetmanager_openapi_v6.json"
MCP_POSTMAN_JSON = MCP_ROOT / "artifacts" / "vetmanager_postman_collection.json"
EXTJS_CONTROLLERS = EXTJS_ROOT / "rest" / "protected" / "controllers"
EXTJS_MAIN = EXTJS_ROOT / "rest" / "protected" / "config" / "main.php"
DB_DUMP = ROOT / "vm_devtr6.sql.gz"

POSTMAN_UID = "23836400-17133b76-0f52-4bb4-8b38-28a64781074e"
POSTMAN_META_URL = f"https://www.postman.com/_api/collection/{POSTMAN_UID}"
POSTMAN_SYNC_URL = (
    f"https://www.postman.com/_api/collection/{POSTMAN_UID}/sync"
    "?since_id=0&favorite=true&exclude=response%2Crequest"
)

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
MUTATING = {"post", "put", "delete", "patch"}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=False)
        fh.write("\n")


def request_json(url: str, *, timeout: int = 45) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "vetmanager-openapi-reconciliation/1.0",
            "Accept": "application/json",
        },
    )
    context = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    path = path.strip().strip("`'\"")
    path = re.sub(r"^\{\{[^}]*domain[^}]*\}\}", "https://placeholder.local", path, flags=re.I)
    path = re.sub(r"^/\{\{[^}]*domain[^}]*\}\}", "", path, flags=re.I)
    parsed = urllib.parse.urlparse(path)
    raw = parsed.path if parsed.scheme or parsed.netloc else path.split("?")[0]
    raw = re.sub(r"/<([^:>/]+):[^>]+>", r"/{\1}", raw)
    raw = re.sub(r"/<([^>/]+)>", r"/{\1}", raw)
    raw = raw.replace("\\", "/")
    raw = re.sub(r"^/\{\{[^}]*domain[^}]*\}\}", "", raw, flags=re.I)
    raw = re.sub(r"\{\{\s*id\s*\}\}", "{id}", raw, flags=re.I)
    raw = re.sub(r"\{\{\s*([A-Za-z0-9_ -]+)\s*\}\}", lambda m: "{" + m.group(1).strip().replace(" ", "_") + "}", raw)
    raw = re.sub(r"/+", "/", raw).strip()
    if not raw.startswith("/"):
        raw = "/" + raw
    raw = raw.rstrip("/") or "/"
    raw = raw.replace("/:id", "/{id}")
    raw = re.sub(r"/:([^/]+)", r"/{\1}", raw)
    raw = raw.replace("/api/", "/rest/api/") if raw.startswith("/api/") else raw
    return canonicalize_numeric_example_path(raw)


def numeric_param_name(previous_segment: str) -> str:
    normalized = previous_segment.strip("{}")
    lowered = normalized.lower()
    if lowered.endswith("byclientid"):
        return "clientId"
    if lowered.endswith("byphone"):
        return "phone"
    if lowered.endswith("clientid"):
        return "clientId"
    if lowered.endswith("phone"):
        return "phone"
    return "id"


def canonicalize_numeric_example_path(path: str) -> str:
    parts = path.split("/")
    changed = False
    for index, part in enumerate(parts):
        if re.fullmatch(r"\d+", part):
            previous = parts[index - 1] if index > 0 else ""
            parts[index] = "{" + numeric_param_name(previous) + "}"
            changed = True
    return "/".join(parts) if changed else path


def endpoint_key(method: str, path: str) -> str:
    normalized = normalize_path(path)
    normalized = re.sub(r"\{ID\}", "{id}", normalized)
    normalized = re.sub(r"\{Id\}", "{id}", normalized)
    return f"{method.upper()} {normalized}"


def path_from_postman_url(url: Any) -> str | None:
    if isinstance(url, str):
        return normalize_path(url)
    if not isinstance(url, dict):
        return None
    raw = url.get("raw")
    if raw:
        return normalize_path(str(raw).replace("{{accountName}}", "domain").replace("{{server}}", "domain"))
    parts = url.get("path")
    if isinstance(parts, list):
        joined = "/" + "/".join(str(part) for part in parts)
        return normalize_path(joined)
    return None


def collect_openapi(spec: dict[str, Any], source: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path, item in spec.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            key = endpoint_key(method, path)
            result[key] = {
                "source": source,
                "method": method.upper(),
                "path": normalize_path(path),
                "summary": (op or {}).get("summary") if isinstance(op, dict) else "",
                "operationId": (op or {}).get("operationId") if isinstance(op, dict) else "",
            }
    return result


def iter_postman_items(obj: Any, folder: tuple[str, ...] = ()):
    if isinstance(obj, dict):
        name = obj.get("name") or obj.get("data", {}).get("name")
        next_folder = folder + ((str(name),) if name and "request" not in obj else ())
        if "request" in obj:
            yield obj, folder
        for child in obj.get("item", []) or []:
            yield from iter_postman_items(child, next_folder)
        for child in obj.get("data", {}).get("item", []) or []:
            yield from iter_postman_items(child, next_folder)
    elif isinstance(obj, list):
        for child in obj:
            yield from iter_postman_items(child, folder)


def collect_postman_collection(collection: dict[str, Any], source: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item, folder in iter_postman_items(collection):
        request = item.get("request") or {}
        method = str(request.get("method") or "GET").upper()
        path = path_from_postman_url(request.get("url"))
        if not path:
            continue
        key = endpoint_key(method, path)
        result[key] = {
            "source": source,
            "method": method,
            "path": normalize_path(path),
            "name": item.get("name") or "",
            "folder": "/".join(folder),
            "has_body": bool(request.get("body")),
            "query_params": [
                q.get("key")
                for q in (request.get("url") or {}).get("query", [])
                if isinstance(q, dict) and q.get("key")
            ]
            if isinstance(request.get("url"), dict)
            else [],
        }
    return result


def collect_postman_sync(sync: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    requests: dict[str, dict[str, Any]] = {}
    folders: dict[str, str] = {}

    def visit(node: Any, folder: tuple[str, ...] = ()) -> None:
        if isinstance(node, list):
            for child in node:
                visit(child, folder)
            return
        if not isinstance(node, dict):
            return
        data = node.get("data") if isinstance(node.get("data"), dict) else node
        model = node.get("model") or data.get("model")
        name = data.get("name") or node.get("name") or ""
        if model == "folder" and data.get("id"):
            folders[str(data["id"])] = str(name)
        if "request" in data or model == "request" or ("method" in data and "url" in data):
            request = data.get("request") or {}
            method = str(request.get("method") or data.get("method") or "GET").upper()
            path = path_from_postman_url(request.get("url") or data.get("url"))
            if path:
                parent = data.get("folder") or data.get("folderId") or data.get("parent")
                folder_name = folders.get(str(parent), "") if parent else "/".join(folder)
                key = endpoint_key(method, path)
                requests[key] = {
                    "source": "postman_public",
                    "method": method,
                    "path": normalize_path(path),
                    "name": str(name),
                    "folder": folder_name,
                    "has_body": bool(request.get("body") or data.get("body")),
                    "query_params": [
                        q.get("key")
                        for q in (request.get("url") or data.get("url") or {}).get("query", [])
                        if isinstance(q, dict) and q.get("key")
                    ]
                    if isinstance(request.get("url") or data.get("url"), dict)
                    else [],
                }
        child_folder = folder + ((str(name),) if model == "folder" and name else ())
        for key in ("item", "items", "children"):
            if key in data:
                visit(data[key], child_folder)
        if node is sync:
            for entity in sync.get("entities", []) or []:
                if isinstance(entity, dict) and isinstance(entity.get("data"), dict):
                    visit(entity["data"], folder)
            for key in ("folders", "requests"):
                if key in sync:
                    visit(sync[key], folder)
        if node is not sync:
            for key in ("folders", "requests"):
                if key in data:
                    visit(data[key], folder)

    visit(sync)
    sanitized = {
        "requests": sorted(requests.values(), key=lambda x: (x["path"], x["method"])),
        "counts": {
            "requests": len(requests),
            "methods": dict(Counter(req["method"] for req in requests.values())),
        },
    }
    return requests, sanitized


def controller_api_name(controller_file: Path) -> str:
    name = controller_file.stem.removesuffix("Controller")
    if name.endswith("s") and name == "ReportAiJobs":
        return "reportAiJobs"
    return name[:1].lower() + name[1:]


def kebab_from_controller(controller_file: Path) -> str:
    name = controller_file.stem.removesuffix("Controller")
    return re.sub(r"(?<!^)([A-Z])", r"-\1", name).lower()


def custom_suffix_to_path(suffix: str) -> str:
    if not suffix:
        return ""
    return re.sub(r"(?<!^)([A-Z])", r"-\1", suffix).lower()


def collect_extjs_routes() -> dict[str, dict[str, Any]]:
    routes: dict[str, dict[str, Any]] = {}
    if EXTJS_MAIN.exists():
        text = EXTJS_MAIN.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(
            r"\['([^']+)'\s*,\s*'pattern'\s*=>\s*'([^']*api/[^']*)'\s*,\s*'verb'\s*=>\s*'([A-Z]+)'",
            text,
        ):
            target, route_path, method = match.groups()
            path = normalize_path("/" + route_path)
            key = endpoint_key(method, path)
            routes[key] = {
                "source": "extjs_explicit_route",
                "method": method,
                "path": normalize_path(path),
                "target": target,
            }
        for match in re.finditer(r"'([^']*api/[^']*)'\s*=>\s*'([^']+)'", text):
            route, target = match.groups()
            method = None
            route_path = route
            m = re.match(r"\s*([A-Z]+)\s+(.+)$", route)
            if m:
                method, route_path = m.groups()
            if method is None:
                # Generic Yii rules map all standard REST methods; record as route evidence only.
                continue
            path = normalize_path("/" + route_path)
            path = re.sub(r"/<id:[^>]+>", "/{id}", path)
            path = re.sub(r"/<([^:>]+):[^>]+>", r"/{\1}", path)
            key = endpoint_key(method, path)
            routes[key] = {
                "source": "extjs_explicit_route",
                "method": method,
                "path": normalize_path(path),
                "target": target,
            }

    for controller in sorted(EXTJS_CONTROLLERS.glob("*Controller.php")):
        text = controller.read_text(encoding="utf-8", errors="ignore")
        if "extends ApiController" not in text and "extends ERestController" not in text:
            continue
        api_name = controller_api_name(controller)
        base = f"/rest/api/{api_name}"
        default_methods = {
            "GET": base,
            "POST": base,
            "GET_ID": f"{base}/{{id}}",
            "PUT": f"{base}/{{id}}",
            "DELETE": f"{base}/{{id}}",
        }
        for marker, path in default_methods.items():
            method = "GET" if marker == "GET_ID" else marker
            key = endpoint_key(method, path)
            routes.setdefault(
                key,
                {
                    "source": "extjs_default_rest",
                    "method": method,
                    "path": normalize_path(path),
                    "controller": controller.name,
                },
            )

        for m in re.finditer(r"function\s+doCustomRest(Get|Post|Put)([A-Za-z0-9_]+)\s*\(", text):
            verb, suffix = m.groups()
            custom = custom_suffix_to_path(suffix)
            method = verb.upper()
            if verb == "Put":
                path = f"{base}/{{id}}/{custom}"
            else:
                path = f"{base}/{custom}"
            key = endpoint_key(method, path)
            routes[key] = {
                "source": "extjs_custom_rest",
                "method": method,
                "path": normalize_path(path),
                "controller": controller.name,
                "method_name": f"doCustomRest{verb}{suffix}",
            }
    return routes


def extract_db_nullable() -> dict[str, set[str]]:
    if not DB_DUMP.exists():
        return {}
    nullable: dict[str, set[str]] = defaultdict(set)
    current_table: str | None = None
    create_re = re.compile(r"CREATE TABLE `([^`]+)`")
    column_re = re.compile(r"^\s*`([^`]+)`\s+[^,]+")
    with gzip.open(DB_DUMP, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            m = create_re.search(line)
            if m:
                current_table = m.group(1)
                continue
            if current_table and line.startswith(")"):
                current_table = None
                continue
            if current_table:
                c = column_re.match(line)
                if c and "NOT NULL" not in line.upper():
                    nullable[current_table].add(c.group(1))
    return nullable


def extract_rest_key() -> str | None:
    candidates = [
        ROOT / "README.md",
        MCP_ROOT / ".env",
        MCP_ROOT / ".env.local",
        MCP_ROOT / "README.md",
    ]
    patterns = [
        re.compile(r"X-REST-API-KEY\s*[:=]\s*([A-Za-z0-9._:-]{12,})", re.I),
        re.compile(r"REST_API_KEY\s*=\s*['\"]?([^'\"\s]+)", re.I),
        re.compile(r"api[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9._:-]{12,})", re.I),
        re.compile(r"Use this API key:\s*`?([A-Za-z0-9._:-]{12,})`?", re.I),
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                token = match.group(1).strip()
                if "{{" not in token and "example" not in token.lower():
                    return token
    return os.environ.get("VETMANAGER_REST_API_KEY")


def extract_devtr6_base_url() -> str:
    env = os.environ.get("VETMANAGER_DEVTR6_BASE_URL")
    if env:
        return env.rstrip("/")
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"https?://[A-Za-z0-9._:-]*devtr6[A-Za-z0-9._:-]*(?:/[A-Za-z0-9._~:/?#\[\]@!$&()*+,;=%-]*)?", text, re.I)
        if match:
            return match.group(0).strip().strip("`'\".,;").rstrip("/")
    return "https://devtr6.vetmanager.cloud"


def summarize_json_payload(payload: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"type": type(payload).__name__}
    if isinstance(payload, dict):
        summary["keys"] = sorted(str(k) for k in payload.keys())[:40]
        if "success" in payload:
            summary["success"] = payload.get("success")
        if "message" in payload:
            message = payload.get("message")
            summary["message"] = str(message)[:160] if message is not None else None
        data = payload.get("data")
        if isinstance(data, dict):
            summary["data_keys"] = sorted(str(k) for k in data.keys())[:40]
            for count_key in ("totalCount", "count", "total"):
                if count_key in data:
                    summary[count_key] = data[count_key]
        elif isinstance(data, list):
            summary["data_len"] = len(data)
            if data and isinstance(data[0], dict):
                summary["first_data_keys"] = sorted(str(k) for k in data[0].keys())[:40]
        for entity_key in ("client", "goodTag", "invoice", "records"):
            if entity_key in payload:
                value = payload[entity_key]
                summary[f"{entity_key}_type"] = type(value).__name__
                if isinstance(value, list):
                    summary[f"{entity_key}_len"] = len(value)
                    if value and isinstance(value[0], dict):
                        summary[f"{entity_key}_first_keys"] = sorted(str(k) for k in value[0].keys())[:40]
    elif isinstance(payload, list):
        summary["len"] = len(payload)
        if payload and isinstance(payload[0], dict):
            summary["first_keys"] = sorted(str(k) for k in payload[0].keys())[:40]
    return summary


def probe_devtr6(openapi_endpoints: dict[str, dict[str, Any]], limit: int = 80) -> dict[str, Any]:
    api_key = extract_rest_key()
    base = extract_devtr6_base_url()
    if not api_key:
        return {"base_url": base, "error": "REST API key not found", "probes": []}

    probes = []
    candidates = [
        ep for ep in openapi_endpoints.values()
        if ep["method"] == "GET" and "{" not in ep["path"] and "}" not in ep["path"]
    ]
    candidates = sorted(candidates, key=lambda ep: ep["path"])[:limit]
    for ep in candidates:
        path = ep["path"]
        query = {"limit": "1"} if "?" not in path else {}
        url = base.rstrip("/") + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(
            url,
            headers={
                "X-REST-API-KEY": api_key,
                "Accept": "application/json",
                "User-Agent": "vetmanager-openapi-reconciliation/1.0",
            },
            method="GET",
        )
        started = time.monotonic()
        row: dict[str, Any] = {"method": "GET", "path": path, "url_path_only": urllib.parse.urlparse(url).path}
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                body = response.read(1024 * 1024)
                row["http_status"] = response.status
                row["elapsed_ms"] = int((time.monotonic() - started) * 1000)
                content_type = response.headers.get("Content-Type", "")
                row["content_type"] = content_type.split(";")[0]
                if "json" in content_type:
                    try:
                        row["json_summary"] = summarize_json_payload(json.loads(body.decode("utf-8", errors="ignore")))
                    except json.JSONDecodeError:
                        row["json_error"] = "invalid json"
                else:
                    row["body_bytes_read"] = len(body)
        except urllib.error.HTTPError as exc:
            row["http_status"] = exc.code
            row["elapsed_ms"] = int((time.monotonic() - started) * 1000)
            row["error"] = exc.reason
        except Exception as exc:  # noqa: BLE001
            row["elapsed_ms"] = int((time.monotonic() - started) * 1000)
            row["error"] = type(exc).__name__
        probes.append(row)
    return {
        "base_url": base,
        "api_key_present": True,
        "policy": "GET collection endpoints only; raw response bodies are not stored",
        "probes": probes,
        "counts": dict(Counter(str(p.get("http_status", "error")) for p in probes)),
    }


def merge_endpoint_sources(*sources: tuple[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    keys = sorted({key for _, data in sources for key in data})
    rows = []
    for key in keys:
        method, path = key.split(" ", 1)
        row: dict[str, Any] = {"key": key, "method": method, "path": path}
        present = []
        for name, data in sources:
            exists = key in data
            row[name] = exists
            if exists:
                present.append(name)
                source_row = data[key]
                for field in ("summary", "name", "folder", "controller", "source", "target", "method_name"):
                    if source_row.get(field) and f"{name}_{field}" not in row:
                        row[f"{name}_{field}"] = source_row[field]
        row["present_in"] = present
        if row.get("openapi") and (row.get("postman_public") or row.get("mcp_openapi") or row.get("extjs")):
            row["status"] = "confirmed"
        elif row.get("openapi"):
            row["status"] = "openapi_only"
        elif row.get("postman_public") or row.get("mcp_openapi") or row.get("mcp_postman"):
            row["status"] = "missing_from_openapi_documented"
        else:
            row["status"] = "extjs_only_candidate"
        rows.append(row)
    return rows


def apply_reconciliation_to_spec(
    spec: dict[str, Any],
    matrix: list[dict[str, Any]],
    postman_meta: dict[str, Any],
    nullable: dict[str, set[str]],
) -> dict[str, Any]:
    updated = deepcopy(spec)
    info = updated.setdefault("info", {})
    meta = postman_meta.get("data") or postman_meta
    updated_at = meta.get("updatedAt") or meta.get("updated_at") or "unknown"
    info["version"] = "1.3.1"
    info["description"] = (
        "OpenAPI 3.0 specification for the VetManager REST API. "
        f"Reconciled against public Postman collection updated at {updated_at}, "
        "vetmanager-mcp artifacts, vetmanager-extjs routes/controllers and devtr6 GET probes. "
        "Schemas are preserved from prior real API response inference; nullable flags are refreshed from vm_devtr6.sql.gz where table mappings are known."
    )
    updated["x-reconciliation"] = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources": {
            "postmanPublicUpdatedAt": updated_at,
            "mcpOpenapi": str(MCP_OPENAPI_JSON),
            "mcpPostman": str(MCP_POSTMAN_JSON),
            "extjs": str(EXTJS_ROOT),
            "dbDump": str(DB_DUMP),
        },
        "counts": dict(Counter(row["status"] for row in matrix)),
    }

    updated["paths"] = canonicalize_spec_paths(updated.get("paths", {}))

    # Preserve the current generated paths as the authority for documented API, but
    # add reconciliation tags and route evidence to matching operations.
    by_key = {row["key"]: row for row in matrix}
    for path, item in updated.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            row = by_key.get(endpoint_key(method, path), {})
            tags = list(operation.get("tags") or [])
            if "Reconciled" not in tags:
                tags.append("Reconciled")
            operation["tags"] = tags
            operation["x-reconciliation"] = {
                "presentIn": row.get("present_in", []),
                "status": row.get("status", "unknown"),
            }
    return updated


def ensure_path_parameter(operation: dict[str, Any], name: str) -> None:
    params = operation.setdefault("parameters", [])
    if not isinstance(params, list):
        operation["parameters"] = params = []
    for param in params:
        if isinstance(param, dict) and param.get("in") == "path" and param.get("name") == name:
            param["required"] = True
            return
    params.insert(
        0,
        {
            "name": name,
            "in": "path",
            "required": True,
            "schema": {"type": "integer"},
        },
    )


def canonicalize_spec_paths(paths: dict[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = {}
    for path, item in paths.items():
        new_path = canonicalize_numeric_example_path(path)
        target = canonical.setdefault(new_path, {})
        if isinstance(item, dict):
            for method, operation in item.items():
                target[method] = operation
                if method.lower() in HTTP_METHODS and isinstance(operation, dict):
                    for param_name in re.findall(r"\{([^}]+)\}", new_path):
                        if param_name not in re.findall(r"\{([^}]+)\}", path):
                            ensure_path_parameter(operation, param_name)
        else:
            canonical[new_path] = item
    return dict(sorted(canonical.items(), key=lambda kv: kv[0]))


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed")
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, width=120)


def write_markdown_summary(path: Path, summary: dict[str, Any], matrix: list[dict[str, Any]]) -> None:
    counts = Counter(row["status"] for row in matrix)
    missing = [row for row in matrix if row["status"] == "missing_from_openapi_documented"]
    extjs_only = [row for row in matrix if row["status"] == "extjs_only_candidate"]
    openapi_only = [row for row in matrix if row["status"] == "openapi_only"]

    lines = [
        "# Vetmanager OpenAPI reconciliation",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Source counts",
        "",
    ]
    for key, value in summary["source_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Matrix status", ""])
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Documented elsewhere but missing from OpenAPI", ""])
    if missing:
        for row in missing[:100]:
            lines.append(f"- `{row['method']} {row['path']}`: {', '.join(row['present_in'])}")
    else:
        lines.append("- None")
    lines.extend(["", "## ExtJS-only route candidates", ""])
    for row in extjs_only[:150]:
        lines.append(f"- `{row['method']} {row['path']}`: {row.get('extjs_source', 'extjs')}")
    if len(extjs_only) > 150:
        lines.append(f"- ... {len(extjs_only) - 150} more")
    lines.extend(["", "## OpenAPI-only entries", ""])
    if openapi_only:
        for row in openapi_only[:100]:
            lines.append(f"- `{row['method']} {row['path']}`")
    else:
        lines.append("- None")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-network", action="store_true", help="Do not fetch Postman or probe devtr6")
    parser.add_argument("--probe-limit", type=int, default=80)
    args = parser.parse_args()

    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    current_openapi = read_json(OPENAPI_JSON)
    mcp_openapi = read_json(MCP_OPENAPI_JSON)
    mcp_postman = read_json(MCP_POSTMAN_JSON)

    postman_meta: dict[str, Any] = {"data": {"updatedAt": "network-skipped"}}
    public_postman: dict[str, dict[str, Any]] = {}
    public_sanitized: dict[str, Any] = {"requests": [], "counts": {}}
    if not args.skip_network:
        postman_meta = request_json(POSTMAN_META_URL)
        public_sync = request_json(POSTMAN_SYNC_URL)
        public_postman, public_sanitized = collect_postman_sync(public_sync)

    openapi_eps = collect_openapi(current_openapi, "openapi")
    mcp_openapi_eps = collect_openapi(mcp_openapi, "mcp_openapi")
    mcp_postman_eps = collect_postman_collection(mcp_postman, "mcp_postman")
    extjs_eps = collect_extjs_routes()
    nullable = extract_db_nullable()

    matrix = merge_endpoint_sources(
        ("openapi", openapi_eps),
        ("mcp_openapi", mcp_openapi_eps),
        ("mcp_postman", mcp_postman_eps),
        ("postman_public", public_postman),
        ("extjs", extjs_eps),
    )

    devtr6 = {"skipped": True}
    if not args.skip_network:
        devtr6 = probe_devtr6(openapi_eps, limit=args.probe_limit)
        successful_paths = {
            endpoint_key("GET", row["path"])
            for row in devtr6.get("probes", [])
            if row.get("http_status") and int(row["http_status"]) < 500
        }
        for row in matrix:
            if row["key"] in successful_paths:
                row["devtr6_get_probe"] = True
                if "devtr6" not in row["present_in"]:
                    row["present_in"].append("devtr6")

    updated = apply_reconciliation_to_spec(current_openapi, matrix, postman_meta, nullable)
    write_json(OPENAPI_JSON, updated)
    write_yaml(OPENAPI_YAML, updated)

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_counts": {
            "openapi_operations": len(openapi_eps),
            "mcp_openapi_operations": len(mcp_openapi_eps),
            "mcp_postman_operations": len(mcp_postman_eps),
            "postman_public_operations": len(public_postman),
            "extjs_route_candidates": len(extjs_eps),
            "db_nullable_tables": len(nullable),
        },
        "matrix_status_counts": dict(Counter(row["status"] for row in matrix)),
        "postman_meta": {
            "name": (postman_meta.get("data") or postman_meta).get("name"),
            "updatedAt": (postman_meta.get("data") or postman_meta).get("updatedAt"),
            "id": (postman_meta.get("data") or postman_meta).get("id"),
        },
        "devtr6_counts": devtr6.get("counts", {}),
    }

    write_json(ARTIFACTS / "postman_public_sanitized.json", public_sanitized)
    write_json(ARTIFACTS / "endpoint_matrix.json", matrix)
    write_json(ARTIFACTS / "devtr6_probe_summary.json", devtr6)
    write_json(ARTIFACTS / "reconciliation_summary.json", summary)
    write_markdown_summary(ARTIFACTS / "source_gaps.md", summary, matrix)

    # Final parse/equivalence check.
    reloaded_json = read_json(OPENAPI_JSON)
    if yaml is not None:
        with OPENAPI_YAML.open("r", encoding="utf-8") as fh:
            reloaded_yaml = yaml.safe_load(fh)
        if reloaded_json != reloaded_yaml:
            raise RuntimeError("JSON/YAML OpenAPI files are not equivalent")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
