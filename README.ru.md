# Спецификация VetManager OpenAPI

[English](README.md) | [Русский](README.ru.md)

Этот репозиторий содержит публичную спецификацию OpenAPI 3.0 для VetManager REST API и небольшой набор инструментов для её сверки с исходными источниками.

Основные артефакты:

- `vetmanager_openapi_v6.yaml` — основная спецификация OpenAPI, используемая Swagger UI.
- `vetmanager_openapi_v6.json` — эквивалент той же спецификации в формате JSON.
- `scripts/reconcile_openapi.py` — сверка с Postman, артефактами MCP, исходниками ExtJS API, необязательным дампом базы данных и проверочными запросами к devtr6.
- `scripts/validate_openapi.py` — локальная и CI-проверка сохранённой спецификации.
- `artifacts/reconciliation/` — очищенные результаты последнего запуска сверки.

Полезные ссылки:

- Публичная коллекция Postman: https://www.postman.com/vetmanager/vetmanager-api/collection/x5iqwq5/vetmanager-collection
- Официальная документация API: https://help.vetmanager.ru/article/25187

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

Процедура сопоставляет сохранённую спецификацию со следующими источниками:

- публичной коллекцией Postman, загружаемой через Postman API;
- OpenAPI/Postman-артефактами `vetmanager-mcp`;
- REST-маршрутами и контроллерами `vetmanager-extjs`;
- необязательным дампом `vm_devtr6.sql.gz` для определения `nullable`;
- необязательными проверочными GET-запросами к devtr6.

Ожидаемая структура локальных каталогов:

```text
/home/otis/myprojects/
  vetmanager-openapi/
  vetmanager-mcp/
  vetmanager-extjs/
```

Стандартный запуск из этого репозитория:

```bash
VETMANAGER_REST_API_KEY=... \
VETMANAGER_DEVTR6_BASE_URL=https://devtr6.vetmanager2.ru \
python3 scripts/reconcile_openapi.py --dump ./vm_devtr6.sql.gz
```

Переносимый вариант с явным указанием путей:

```bash
VETMANAGER_REST_API_KEY=... \
python3 scripts/reconcile_openapi.py \
  --openapi-root /path/to/vetmanager-openapi \
  --mcp-root /path/to/vetmanager-mcp \
  --extjs-root /path/to/vetmanager-extjs \
  --dump /path/to/vm_devtr6.sql.gz
```

Автономная сверка без обращений к Postman и devtr6:

```bash
python3 scripts/reconcile_openapi.py --skip-network
```

Параметр `--skip-network` отключает только загрузку Postman и проверочные запросы к devtr6. Для запуска по-прежнему нужны локальные артефакты `vetmanager-mcp` и исходники `vetmanager-extjs` из приведённой выше структуры. Если требуется лишь проверить уже подготовленное изменение спецификации, используйте `scripts/validate_openapi.py`.

Требования безопасности:

- Не добавляйте в репозиторий `.sql`, `.sql.gz`, необработанные экспорты Postman, исходные ответы API, `.env` и секреты.
- Скрипт сверки сохраняет только очищенные метаданные Postman.
- Артефакты проверок devtr6 содержат только краткие сведения о статусе и структуре JSON, но не исходные тела ответов.
- `VETMANAGER_REST_API_KEY` должен передаваться через переменные окружения или секреты CI.

## Артефакты сверки

В репозитории хранится только последний очищенный снимок результатов сверки:

- `reconciliation_summary.json` — количество источников и статусов;
- `endpoint_matrix.json` — наличие пар «метод/путь» в разных источниках;
- `postman_public_sanitized.json` — метаданные публичных методов и путей Postman без исходных ответов;
- `devtr6_probe_summary.json` — статусы GET-проверок и краткое описание структуры JSON;
- `source_gaps.md` — читаемая сводка пробелов документации и маршрутов-кандидатов только из ExtJS.

Необработанные данные Postman и исходные ответы API намеренно не сохраняются.

## Обновление Swagger UI

Workflow `.github/workflows/update-swagger.yml` обновляет встроенную версию Swagger UI, а затем восстанавливает `dist/swagger-initializer.js` из постоянного шаблона `scripts/swagger-initializer.js`. Шаблон содержит ссылку:

```javascript
url: "vetmanager_openapi_v6.yaml"
```

В шаблоне также хранится сортировка операций GET → POST → PUT → DELETE. Проверка контролирует ссылку, наличие `operationsSorter` и полное совпадение шаблона с файлом в `dist`, поэтому автоматическое обновление Swagger UI не может незаметно удалить настройки проекта.
