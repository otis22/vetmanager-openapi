function clinicAddress(value) {
  const raw = value.trim();
  if (!raw || /\s/.test(raw)) {
    throw new Error("Укажите адрес вашей клиники.");
  }
  let url;
  try {
    url = new URL(raw.includes("://") ? raw : "https://" + raw);
  } catch (_) {
    throw new Error("Проверьте адрес клиники, например one.localhost:8080.");
  }
  if (!/^https?:$/.test(url.protocol) || url.username || url.password
      || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("Укажите адрес клиники без пути запроса, логина и параметров.");
  }
  const local = url.hostname === "localhost" || url.hostname.endsWith(".localhost")
    || url.hostname === "127.0.0.1" || url.hostname === "[::1]";
  return { host: url.host, local: local };
}

window.onload = function() {
  const methodOrder = {
    get: 0,
    post: 1,
    put: 2,
    delete: 3,
    patch: 4,
    options: 5,
    head: 6,
    trace: 7
  };

  window.ui = SwaggerUIBundle({
    url: "vetmanager_openapi_v6.yaml",
    dom_id: '#swagger-ui',
    deepLinking: true,
    persistAuthorization: true,
    showMutatedRequest: true,
    requestInterceptor: function(request) {
      if (request.loadSpec || !window.ui) {
        return request;
      }
      const system = window.ui.getSystem();
      const server = system.oas3Selectors.selectedServer();
      if (server === "https://{domain}") {
        const address = clinicAddress(system.oas3Selectors.serverVariableValue(server, "domain") || "");
        if (address.local && window.VETMANAGER_LOCAL_PROXY) {
          const url = new URL(request.url);
          request.url = window.location.origin + "/__local_api/" + encodeURIComponent(address.host)
            + url.pathname + url.search;
        }
      }
      return request;
    },
    validatorUrl: null,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl,
      function clinicDomainField(system) {
        const React = system.React;
        return {
          components: {
            InfoUrl: function SpecDownload(props) {
              return React.createElement("div", { className: "spec-download" },
                React.createElement("a", { href: props.url }, "Спецификация API (OpenAPI YAML)"),
                React.createElement("p", null,
                  "Описание API для импорта в Postman и другие инструменты."),
                React.createElement("a", { className: "docs-button spec-faq-link", href: "./faq.html" },
                  "FAQ по API", React.createElement("span", { "aria-hidden": "true" }, "→")),
                " ",
                React.createElement("a", { className: "docs-button spec-faq-link", href: "./releases.html" },
                  "Изменения API по релизам", React.createElement("span", { "aria-hidden": "true" }, "→"))
              );
            }
          },
          wrapComponents: {
            execute: function(Original) {
              return function ClinicExecute(props) {
                return React.createElement("div", {
                  style: { display: "contents" },
                  onClickCapture: function(event) {
                    const server = system.oas3Selectors.selectedServer();
                    if (server !== "https://{domain}") return;
                    const input = document.getElementById("clinic-domain");
                    try {
                      const address = clinicAddress(system.oas3Selectors.serverVariableValue(server, "domain") || "");
                      if (address.local && !window.VETMANAGER_LOCAL_PROXY) {
                        throw new Error("Для локального API откройте предпросмотр, запущенный через python3 scripts/serve_docs.py.");
                      }
                      system.oas3Actions.setServerVariableValue({ server: server, key: "domain", val: address.host });
                      if (input) input.setCustomValidity("");
                    } catch (error) {
                      event.preventDefault();
                      event.stopPropagation();
                      if (input) {
                        input.setCustomValidity(error.message);
                        input.reportValidity();
                        input.focus();
                      }
                    }
                  }
                }, React.createElement(Original, props));
              };
            },
            ServersContainer: function(Original) {
              return function ClinicDomainField(props) {
                const servers = props.specSelectors.servers();
                const server = servers && servers.first();
                const supportsDomain = servers && servers.size === 1
                  && server.getIn(["variables", "domain"]);
                const url = supportsDomain ? server.get("url") : "";
                const selected = props.oas3Selectors.selectedServer();
                React.useEffect(function() {
                  if (url && selected !== url) {
                    props.oas3Actions.setSelectedServer(url);
                  }
                }, [url, selected]);
                if (!supportsDomain) {
                  return React.createElement(Original, props);
                }
                const value = props.oas3Selectors.serverVariableValue(url, "domain") ?? "";
                return React.createElement("div", { className: "clinic-domain" },
                  React.createElement("label", { htmlFor: "clinic-domain" }, "Домен вашей клиники"),
                  React.createElement("input", {
                    id: "clinic-domain",
                    type: "text",
                    value: value,
                    placeholder: "devtr6.vetmanager2.ru",
                    autoCapitalize: "none",
                    autoCorrect: "off",
                    spellCheck: false,
                    "aria-describedby": "clinic-domain-help",
                    onChange: function(event) {
                      event.target.setCustomValidity("");
                      props.oas3Actions.setServerVariableValue({
                        server: url, key: "domain", val: event.target.value.trim()
                      });
                    }
                  }),
                  React.createElement("p", { id: "clinic-domain-help", style: { whiteSpace: "pre-line" } },
                    "Введите домен клиники для выполнения запросов к API.\n" +
                    "Для авторизации нажмите Authorize и введите API-ключ клиники в поле X-REST-API-KEY.")
                );
              };
            }
          }
        };
      },
      function alphabeticalSchemas() {
        return {
          statePlugins: {
            spec: {
              wrapSelectors: {
                definitions: function(originalSelector) {
                  return function(state) {
                    const defs = originalSelector(state);
                    if (!defs || typeof defs.sortBy !== "function") {
                      return defs;
                    }
                    return defs.sortBy(function(_value, key) {
                      return String(key).toLowerCase();
                    });
                  };
                }
              }
            }
          }
        };
      }
    ],
    tagsSorter: "alpha",
    operationsSorter: function(a, b) {
      const methodA = a.get("method").toLowerCase();
      const methodB = b.get("method").toLowerCase();
      const orderA = methodOrder[methodA] ?? Number.MAX_SAFE_INTEGER;
      const orderB = methodOrder[methodB] ?? Number.MAX_SAFE_INTEGER;

      if (orderA !== orderB) {
        return orderA - orderB;
      }

      return a.get("path").localeCompare(b.get("path"));
    },
    layout: "StandaloneLayout"
  });
};
