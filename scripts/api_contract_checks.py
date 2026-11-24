"""HTTP contract checks for the public REST list operations."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import urllib.error
import urllib.parse
import urllib.request


LIST_RESOURCES = ("fiscalRegister", "fiscalRegisterData", "invoiceDocument")
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class Check:
    name: str
    method: str
    path: str
    status: int
    query: str = ""
    body: bytes | None = None
    content_type: str | None = None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def json_schema(value):
    if isinstance(value, list):
        return [json_schema(item) for item in value]
    if isinstance(value, dict):
        result = {key: json_schema(item) for key, item in value.items()}
        if result.get("nullable") is True and isinstance(result.get("type"), str):
            result["type"] = [result["type"], "null"]
        return result
    return value


def response_media(spec: dict, check: Check) -> dict:
    response = spec["paths"][check.path][check.method.lower()]["responses"][str(check.status)]
    visited = set()
    while "$ref" in response:
        reference = response["$ref"]
        if not reference.startswith("#/") or reference in visited:
            raise ValueError("Invalid local response reference")
        visited.add(reference)
        response = spec
        for part in reference[2:].split("/"):
            response = response[part.replace("~1", "/").replace("~0", "~")]
    return response["content"]["application/json"]


def request(opener, base: str, key: str, check: Check) -> tuple[int, str, bytes]:
    headers = {"Accept": "application/json", "X-REST-API-KEY": key}
    if check.content_type:
        headers["Content-Type"] = check.content_type
    request = urllib.request.Request(
        base + check.path + check.query, data=check.body, headers=headers, method=check.method,
    )
    try:
        response = opener.open(request, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers.get_content_type(), response.read(MAX_RESPONSE_BYTES + 1)


def validate_response(validator, media: dict, check: Check, response: tuple[int, str, bytes]):
    status, content_type, raw = response
    if status != check.status:
        raise ValueError(f"HTTP {status} вместо {check.status}")
    if content_type != "application/json" or len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("ожидался JSON-ответ размером до 2 MiB")
    try:
        body = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("сервер вернул некорректный JSON") from None
    error = next(validator.evolve(schema=media["schema"]).iter_errors(body), None)
    if error is not None:
        path = ".".join(map(str, error.absolute_path)) or "$"
        raise ValueError(f"схема не совпала в `{path}` (правило `{error.validator}`)")
    if check.status == 200 and (not isinstance(body, dict) or body.get("success") is not True):
        raise ValueError("ожидался успешный ответ")
    if check.status >= 400 and "example" in media and body != media["example"]:
        raise ValueError("тело ошибки отличается от примера в OpenAPI")
    return body


def list_checks(resource: str) -> tuple[Check, ...]:
    path = f"/rest/api/{resource}"
    form = "application/x-www-form-urlencoded"
    query = urllib.parse.urlencode({"limit": 1, "offset": 0, "sort": "id"})
    return (
        Check("GET списка", "GET", path, 200, query="?" + query),
        Check("POST формы", "POST", path + "/list", 200, body=query.encode(), content_type=form),
        Check("POST без тела", "POST", path + "/list", 200),
        Check("JSON вместо формы", "POST", path + "/list", 406, body=b'{"filter":[]}', content_type="application/json"),
        Check("Превышение лимита", "POST", path + "/list", 413, body=b"limit=" + b"1" * 8192, content_type=form),
    )


def run_http_checks(spec: dict, base_url: str) -> tuple[str, int]:
    # The offline preview does not need the optional schema validation dependencies.
    try:
        from jsonschema import Draft4Validator
        from referencing import Registry
    except ImportError as exc:
        raise ValueError("HTTP checks require jsonschema. Install it with python3 -m pip install jsonschema.") from exc

    url = urllib.parse.urlsplit(base_url)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username is not None or url.query or url.fragment:
        raise ValueError("Use an HTTP(S) test URL without credentials, query parameters or fragment")
    key = os.environ.get("VETMANAGER_REST_API_KEY", "")
    if not key:
        raise ValueError("Set VETMANAGER_REST_API_KEY for the test stand")
    spec = json_schema(spec)
    validator = Draft4Validator(spec, registry=Registry())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    base = base_url.rstrip("/")
    lines = ["# HTTP-проверка OpenAPI", "", f"Стенд `{base}`", ""]
    failures = 0

    for resource in LIST_RESOURCES:
        lines.extend([f"## {resource}", ""])
        get_body = None
        for check in list_checks(resource):
            try:
                media = response_media(spec, check)
                body = validate_response(validator, media, check, request(opener, base, key, check))
                note = ""
                if check.method == "GET":
                    get_body = body
                if check.status == 200:
                    rows = body.get("data", {}).get(resource) if isinstance(body.get("data"), dict) else None
                    if not isinstance(rows, list):
                        raise ValueError(f"ожидался массив `data.{resource}`")
                    note = f", записей {len(rows)}"
                if check.name == "POST формы" and get_body is not None and body != get_body:
                    raise ValueError("ответ отличается от GET с теми же параметрами")
                lines.append(f"- OK · {check.name} · HTTP {check.status}{note}")
            except (KeyError, ValueError, OSError) as exc:
                failures += 1
                detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                lines.append(f"- Ошибка · {check.name} · {detail}")
        lines.append("")

    return "\n".join(lines) + "\n", failures
