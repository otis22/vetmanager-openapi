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
    validatorUrl: null,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
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
