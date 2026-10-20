# VetManager OpenAPI Specification

[English](README.md) | [Русский](README.ru.md)

This repository contains the public OpenAPI 3.0 specification for the VetManager REST API and a small maintenance toolchain for reconciling it against upstream sources.

Primary artifacts:

- `vetmanager_openapi_v6.yaml` - primary OpenAPI specification used by Swagger UI.
- `vetmanager_openapi_v6.json` - JSON equivalent of the same specification.
- `scripts/reconcile_openapi.py` - reconciliation flow for ExtJS API sources, an optional DB dump, and devtr6 probes.
- `scripts/validate_openapi.py` - local and CI validation for the committed specification.
- `excluded_routes.md` - working routes intentionally excluded from the public Swagger.
- `artifacts/reconciliation/` - sanitized audit output from the latest reconciliation run.

Useful links:

- Official API documentation: https://help.vetmanager.ru/article/25187

## View Documentation

Run the repository's bundled Swagger UI from the project root:

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080.

This serves the project's `dist/swagger-initializer.js` and loads `vetmanager_openapi_v6.yaml`, so local previews include project UI settings such as GET → POST → PUT → DELETE operation sorting. If port 8080 is occupied by a previously started Docker container, stop it first or use another port, for example `python3 -m http.server 8081`.

## Validate

For ordinary specification or documentation changes, validation is the only
required local command. Create a temporary virtual environment and install the
only Python dependency:

```bash
python3 -m venv /tmp/vetmanager-openapi-venv
/tmp/vetmanager-openapi-venv/bin/pip install pyyaml
```

Then run:

```bash
/tmp/vetmanager-openapi-venv/bin/python scripts/validate_openapi.py
```

The environment under `/tmp` is intentionally outside the repository and can
be removed or recreated at any time. If PyYAML is already installed in the
active Python environment, `python3 scripts/validate_openapi.py` is sufficient.

The validator checks:

- JSON and YAML equivalence.
- Basic OpenAPI structure.
- unique `operationId` values.
- declared path parameters.
- no trailing-slash paths.
- no literal numeric example segments such as `/client/116468`.
- Swagger UI references to `vetmanager_openapi_v6.yaml`.
- no obvious secret literals in README, scripts, or reconciliation artifacts.

The same validation runs in GitHub Actions on pushes and pull requests.

## Reconcile The Specification

Reconciliation is a maintainer workflow, not a prerequisite for every OpenAPI
or README edit. Run it only when endpoint/source reconciliation artifacts need
to be regenerated.

The reconciliation flow compares the committed specification with
`vetmanager-extjs` REST route/controller sources. It can also use an optional
`vm_devtr6.sql.gz` dump for nullable metadata and run devtr6 GET probes.

Expected local layout:

```text
/home/art/Projects/
  vetmanager-openapi/
  vetmanager-extjs/
```

Default run from this repository:

```bash
python3 scripts/reconcile_openapi.py
```

Portable run with explicit paths:

```bash
python3 scripts/reconcile_openapi.py \
  --openapi-root /path/to/vetmanager-openapi \
  --extjs-root /path/to/vetmanager-extjs
```

Skip optional devtr6 probes:

```bash
python3 scripts/reconcile_openapi.py --offline
```

The only required neighbouring repository is `vetmanager-extjs`. Use
`scripts/validate_openapi.py` when only validating an already prepared
specification change.

Security notes:

- Do not commit `.sql`, `.sql.gz`, raw API responses, `.env`, or secrets.
- devtr6 probe artifacts store compact status/shape summaries only, not raw response bodies.
- `VETMANAGER_REST_API_KEY` must come from environment variables or CI secrets.

## Reconciliation Artifacts

The repository keeps only the latest sanitized reconciliation snapshot:

- `reconciliation_summary.json` - source and status counts.
- `endpoint_matrix.json` - method/path presence across sources.
- `devtr6_probe_summary.json` - GET probe status and compact JSON-shape summaries.
- `source_gaps.md` - human-readable summary of documented gaps and ExtJS-only candidates.

Routes listed in `excluded_routes.md` receive the
`intentionally_undocumented` status and do not appear among ExtJS-only
candidates. The registry is the only detailed list; `source_gaps.md` reports
only the status count. Add a route there only after confirming that it must
not be part of the public API contract.

Raw API responses are intentionally not stored.

## Swagger UI Updates

`.github/workflows/update-swagger.yml` updates the bundled Swagger UI dependency and then restores `dist/swagger-initializer.js` from the project-owned `scripts/swagger-initializer.js` template. The template points at:

```javascript
url: "vetmanager_openapi_v6.yaml"
```

The template also owns GET → POST → PUT → DELETE operation sorting. Validation checks the URL, the presence of `operationsSorter`, and exact equality between the template and the generated `dist` file, so an automated Swagger UI update cannot silently remove project settings.
