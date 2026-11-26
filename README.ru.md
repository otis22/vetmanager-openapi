# Спецификация VetManager OpenAPI

[English](README.md) | [Русский](README.ru.md)

Этот репозиторий содержит публичную спецификацию OpenAPI 3.0 для VetManager REST API и небольшой набор инструментов для её сверки с исходными источниками.

Основные артефакты:

- `vetmanager_openapi_v6.yaml` — основная спецификация OpenAPI, используемая Swagger UI.
- `vetmanager_openapi_v6.json` — эквивалент той же спецификации в формате JSON.
- `scripts/reconcile_openapi.py` — сверка с исходниками ExtJS API, необязательным дампом базы данных и проверочными GET-запросами.
- `scripts/validate_openapi.py` — локальная и CI-проверка сохранённой спецификации.
- `artifacts/reconciliation/` — очищенные результаты последнего запуска сверки.

## Просмотр документации

Запустите сохранённый в репозитории Swagger UI локально из корня проекта:

```bash
python3 scripts/serve_docs.py
```

После этого откройте http://localhost:8081.

Чтобы отправить запрос через **Try it out**, укажите домен клиники или локальный адрес `http://one.localhost:8080/`, затем введите API-ключ через **Authorize**. Сервер предпросмотра позволяет отправлять запросы к локальному API без настройки CORS.

Если порт 8081 занят, запустите `python3 scripts/serve_docs.py --port 8091` и откройте http://localhost:8091/.

## Проверка

Для проверки спецификации запустите из корня репозитория:

```bash
python3 scripts/validate_openapi.py
```

Если валидатор вернул `"valid": true`, проверка завершена.

Если отсутствует PyYAML, установите его в отдельное окружение и запустите валидатор из него:

```bash
python3 -m venv /tmp/vetmanager-openapi-venv &&
  /tmp/vetmanager-openapi-venv/bin/python -m pip install PyYAML &&
  /tmp/vetmanager-openapi-venv/bin/python scripts/validate_openapi.py
```

Если при создании окружения Debian или Ubuntu сообщает `ensurepip is not available`, установите пакет для версии Python, указанной в сообщении об ошибке. Например, для Python 3.14 выполните:

```bash
sudo apt install python3.14-venv
```

После установки повторите команды создания окружения и запуска валидатора.

Валидатор проверяет:

- эквивалентность JSON и YAML;
- базовую структуру OpenAPI;
- уникальность значений `operationId`;
- объявление параметров пути;
- отсутствие путей с завершающим `/`;
- отсутствие конкретных числовых идентификаторов в путях, например `/client/116468`;
- ссылки Swagger UI на `vetmanager_openapi_v6.yaml`;
- отсутствие очевидных секретов в README, скриптах и артефактах сверки.

Та же проверка запускается в GitHub Actions для push и pull request.

## Предпросмотр изменений из ветки бэкенда

Запустите `python3 scripts/preview_sync.py HEAD`, чтобы сравнить текущий коммит бэкенда с рабочей версией спецификации. Можно выбрать ветку, тег или SHA. Diff спецификации и отчёт будут в отдельном каталоге. Команды и следующие шаги описаны в [плане синхронизации](openapi-sync-plan.md). Для HTTP-проверок на тестовом стенде передайте `--api-base-url` и задайте `VETMANAGER_REST_API_KEY` в окружении.

## Сверка спецификации

Сверка — служебная процедура для сопровождающих проект, а не обязательный шаг после каждого изменения OpenAPI или README. Запускайте её только тогда, когда требуется заново сформировать артефакты сверки эндпоинтов и источников.

Процедура сопоставляет сохранённую спецификацию с REST-маршрутами и
контроллерами `vetmanager-extjs`. Дополнительно она может использовать
необязательный дамп `vm_devtr6.sql.gz` для определения `nullable` и выполнять
проверочные GET-запросы.

Ожидаемая структура локальных каталогов:

```text
/home/otis/myprojects/
  vetmanager-openapi/
  vetmanager-extjs/
```

Стандартный запуск из этого репозитория:

```bash
python3 scripts/reconcile_openapi.py
```

Переносимый вариант с явным указанием путей:

```bash
python3 scripts/reconcile_openapi.py \
  --openapi-root /path/to/vetmanager-openapi \
  --extjs-root /path/to/vetmanager-extjs
```

Запуск без необязательных GET-проверок:

```bash
python3 scripts/reconcile_openapi.py --offline
```

Единственный обязательный соседний репозиторий — `vetmanager-extjs`. Если
требуется лишь проверить уже подготовленное изменение спецификации, используйте
`scripts/validate_openapi.py`.

Требования безопасности:

- Не добавляйте в репозиторий `.sql`, `.sql.gz`, исходные ответы API, `.env` и секреты.
- Артефакты проверок devtr6 содержат только краткие сведения о статусе и структуре JSON, но не исходные тела ответов.
- `VETMANAGER_REST_API_KEY` должен передаваться через переменные окружения или секреты CI.

## Артефакты сверки

В репозитории хранится только последний очищенный снимок результатов сверки:

- `reconciliation_summary.json` — количество источников и статусов;
- `endpoint_matrix.json` — наличие пар «метод/путь» в разных источниках;
- `devtr6_probe_summary.json` — статусы GET-проверок и краткое описание структуры JSON;
- `source_gaps.md` — читаемая сводка пробелов документации и маршрутов-кандидатов только из ExtJS.

Исходные ответы API намеренно не сохраняются.

## Обновление Swagger UI

Workflow `.github/workflows/update-swagger.yml` обновляет встроенную версию Swagger UI, а затем восстанавливает `dist/swagger-initializer.js` из постоянного шаблона `scripts/swagger-initializer.js`. Шаблон содержит ссылку:

```javascript
url: "vetmanager_openapi_v6.yaml"
```
