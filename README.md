# VetManager OpenAPI Specification

This repository contains the public OpenAPI 3.0 specification for the VetManager REST API and a small maintenance toolchain for reconciling it against upstream sources.

Primary artifacts:

- `vetmanager_openapi_v6.yaml` - primary OpenAPI specification used by Swagger UI.
- `vetmanager_openapi_v6.json` - JSON equivalent of the same specification.
- `scripts/reconcile_openapi.py` - reconciliation flow for Postman, MCP artifacts, ExtJS API sources, an optional DB dump, and devtr6 probes.
- `scripts/validate_openapi.py` - local and CI validation for the committed specification.
- `artifacts/reconciliation/` - sanitized audit output from the latest reconciliation run.

Useful links:

- Public Postman collection: https://www.postman.com/vetmanager/vetmanager-api/collection/x5iqwq5/vetmanager-collection
- Official API documentation: https://help.vetmanager.ru/article/25187

## View Documentation

Run Swagger UI locally:

```bash
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/openapi/vetmanager_openapi_v6.yaml \
  -v "$(pwd):/openapi" \
  swaggerapi/swagger-ui
```

Then open http://localhost:8080.

The committed static Swagger UI uses `dist/swagger-initializer.js` and loads `vetmanager_openapi_v6.yaml`.

## Validate

Install the only local Python dependency if needed:

```bash
python3 -m pip install pyyaml
```

Run:

```bash
python3 scripts/validate_openapi.py
```

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

The reconciliation flow compares the committed spec with:

- the public Postman collection fetched from Postman APIs.
- `vetmanager-mcp` OpenAPI/Postman artifacts.
- `vetmanager-extjs` REST route/controller sources.
- an optional `vm_devtr6.sql.gz` dump for nullable metadata.
- optional devtr6 GET probes.

Expected local layout:

```text
/home/otis/myprojects/
  vetmanager-openapi/
  vetmanager-mcp/
  vetmanager-extjs/
```

Default run from this repository:

```bash
VETMANAGER_REST_API_KEY=... \
VETMANAGER_DEVTR6_BASE_URL=https://devtr6.vetmanager2.ru \
python3 scripts/reconcile_openapi.py --dump ./vm_devtr6.sql.gz
```

Portable run with explicit paths:

```bash
VETMANAGER_REST_API_KEY=... \
python3 scripts/reconcile_openapi.py \
  --openapi-root /path/to/vetmanager-openapi \
  --mcp-root /path/to/vetmanager-mcp \
  --extjs-root /path/to/vetmanager-extjs \
  --dump /path/to/vm_devtr6.sql.gz
```

Offline reconciliation without Postman/devtr6 network calls:

```bash
python3 scripts/reconcile_openapi.py --skip-network
```

Security notes:

- Do not commit `.sql`, `.sql.gz`, raw Postman exports, raw API responses, `.env`, or secrets.
- The reconciliation script stores sanitized Postman metadata only.
- devtr6 probe artifacts store compact status/shape summaries only, not raw response bodies.
- `VETMANAGER_REST_API_KEY` must come from environment variables or CI secrets.

## Reconciliation Artifacts

The repository keeps only the latest sanitized reconciliation snapshot:

- `reconciliation_summary.json` - source and status counts.
- `endpoint_matrix.json` - method/path presence across sources.
- `postman_public_sanitized.json` - public Postman method/path metadata without raw responses.
- `devtr6_probe_summary.json` - GET probe status and compact JSON-shape summaries.
- `source_gaps.md` - human-readable summary of documented gaps and ExtJS-only candidates.

Raw Postman payloads and raw API responses are intentionally not stored.

## Swagger UI Updates

`.github/workflows/update-swagger.yml` updates the bundled Swagger UI dependency and must keep `dist/swagger-initializer.js` pointing at:

```javascript
url: "vetmanager_openapi_v6.yaml"
```

The validation workflow checks this so an automated Swagger UI update cannot silently switch back to `swagger.yaml`.
