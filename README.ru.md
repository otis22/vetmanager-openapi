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
python3 -m http.server 8080
```

После этого откройте http://localhost:8080.

Этот способ использует `dist/swagger-initializer.js` из проекта и загружает `vetmanager_openapi_v6.yaml`. Поэтому локально применяются настройки интерфейса проекта, включая сортировку операций GET → POST → PUT → DELETE. Если порт 8080 уже занят ранее запущенным Docker-контейнером, сначала остановите его или используйте другой порт, например `python3 -m http.server 8081`.

## Проверка

Для обычных изменений спецификации или документации достаточно выполнить локальную проверку. Создайте временное виртуальное окружение и установите единственную зависимость Python:

```bash
python3 -m venv /tmp/vetmanager-openapi-venv
/tmp/vetmanager-openapi-venv/bin/pip install pyyaml
```

Затем запустите:

```bash
/tmp/vetmanager-openapi-venv/bin/python scripts/validate_openapi.py
```

Окружение находится в `/tmp`, за пределами репозитория, поэтому его можно в любой момент удалить или создать заново. Если PyYAML уже установлен в активном окружении Python, достаточно выполнить `python3 scripts/validate_openapi.py`.

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
