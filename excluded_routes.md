# Исключённые из публичного Swagger

Этот реестр содержит работающие маршруты, которые намеренно не должны
показываться в публичной OpenAPI-спецификации. При запуске
`scripts/reconcile_openapi.py` они получают статус `intentionally_undocumented`
и не попадают в список кандидатов для Swagger.

Формат каждой записи:

```md
- `<METHOD> /path`: причина
```

## Отключённые операции invoice

- `DELETE /rest/api/invoice/{id}`: disabled
- `POST /rest/api/invoice`: disabled
- `PUT /rest/api/invoice/{id}`: disabled

## Отключённые операции invoiceDocument и fiscalRegister

- `POST /rest/api/invoiceDocument`: disabled
- `PUT /rest/api/invoiceDocument/{id}`: disabled
- `DELETE /rest/api/invoiceDocument/{id}`: disabled
- `POST /rest/api/fiscalRegister`: disabled
- `PUT /rest/api/fiscalRegister/{id}`: disabled
- `DELETE /rest/api/fiscalRegister/{id}`: disabled

## API лабораторных провайдеров

- `GET /rest/api/provider-lab-requests/list`: provider_service_api
- `POST /rest/api/provider-lab-requests/result-html`: provider_service_api
- `POST /rest/api/provider-lab-requests/result-values`: provider_service_api
- `POST /rest/api/provider-lab-requests/take`: provider_service_api
- `POST /rest/api/provider-lab-requests/waiting`: provider_service_api

## Внутренние и технические маршруты

- `POST /rest/api/fiscalRegister/evotor-telemetry`: internal_telemetry
- `POST /rest/api/{controller}/list`: framework_route_template
