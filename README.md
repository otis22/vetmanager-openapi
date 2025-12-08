# VetManager API - OpenAPI Specification

This repository contains the OpenAPI 3.0 specification for the VetManager REST API. The specification is generated based on real API responses and is enhanced with nullable information from the database schema.

**Version:** 6.0.0 (Real API Responses)
**Date:** 2025-12-05

## 🔗 Useful Links

- **Postman Collection:** [VetManager API Collection](https://www.postman.com/vetmanager/vetmanager-api/collection/x5iqwq5/vetmanager-collection)
- **Official API Documentation:** [VetManager REST API Documentation](https://help.vetmanager.ru/article/25187)

## 📁 Files in this Repository

- `vetmanager_openapi_v6.yaml`: The primary OpenAPI specification in YAML format.
- `vetmanager_openapi_v6.json`: The same specification in JSON format.
- `README.md`: This file, containing instructions on how to use and update the specification.

## 🚀 How to Use

The OpenAPI specification can be used to generate client SDKs, set up API testing, or create interactive documentation.

### 1. Interactive Documentation with Swagger UI

To view the documentation in a browser, you can use Swagger UI.

```bash
# Run Swagger UI in Docker
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/openapi/vetmanager_openapi_v6.yaml \
  -v $(pwd):/openapi \
  swaggerapi/swagger-ui
```

Then open [http://localhost:8080](http://localhost:8080) in your browser.

### 2. Import into Postman

1. Open Postman.
2. Click **Import**.
3. Select **Upload Files**.
4. Choose either `vetmanager_openapi_v6.yaml` or `vetmanager_openapi_v6.json`.

Postman will automatically create a new collection based on the specification.

### 3. Generate Client SDKs

You can use `openapi-generator-cli` to generate a typed client for your preferred programming language.

```bash
# Example: Generate a Python client
openapi-generator-cli generate \
  -i vetmanager_openapi_v6.yaml \
  -g python \
  --additional-properties=packageName=vetmanager_api

# Example: Generate a TypeScript client
openapi-generator-cli generate \
  -i vetmanager_openapi_v6.yaml \
  -g typescript-axios
```

---

## 🔄 How to Update (Regenerate) the Specification

When the VetManager API is updated, you will need to regenerate this OpenAPI specification. You can delegate this task to an AI agent (like Manus, ChatGPT with Code Interpreter, etc.) using the prompt below.

### Instructions

1. **Export new files:**
   - Export the latest Postman collection as a JSON file.
   - Get a new database dump (`.sql.gz`).
2. **Start a new task** with your AI agent.
3. **Copy and paste** the entire prompt from the section below.
4. **Attach the required files** to the prompt.
5. The agent will perform the necessary steps and provide you with the updated `openapi.yaml` and `openapi.json` files.

---

## 🤖 Prompt for AI Agent Regeneration

**Instructions:** Copy the text below into a new task for your AI agent.

```text
Hello! I need you to update the OpenAPI specification for the VetManager API.

Your task is to create a new OpenAPI 3.0 specification (`openapi.yaml` and `openapi.json`) based on the attached files. Please follow this exact methodology:

**Methodology:**

1.  **Primary Source:** The main source of truth for data types and structure must be **real API responses**.
2.  **Secondary Source:** The database dump should **only** be used for two purposes:
    - To find valid IDs for testing endpoints (e.g., `GET /api/client/{id}`).
    - To determine which fields can be `NULL` (`nullable: true/false`).

**Do not** use the database schema to determine the `type` of a field (e.g., `integer`, `string`). The type must come from the actual JSON response from the API.

**Step-by-Step Plan:**

1.  **Unpack Files:** Unzip the database dump (`.sql.gz`).

2.  **Extract IDs from Database:** Parse the `.sql` file to find valid IDs from `INSERT` statements for as many tables as possible.

3.  **Test API Endpoints:**
    - Parse the attached Postman collection to get a list of all `GET` endpoints.
    - Test as many endpoints as possible (at least 100).
    - For endpoints that require an ID, use the valid IDs you extracted from the database.
    - Use this API key: `600e562402f47b4f24ebca4f02331783` and base URL: `https://devtr6.vetmanager2.ru`.
    - Save all successful responses into a single, comprehensive JSON file (e.g., `api_responses.json`).

4.  **Generate Schemas from API Responses:**
    - Parse the `api_responses.json` file.
    - For each unique entity (e.g., `client`, `admission`, `pet`), create a JSON schema. The `type` of each property must be inferred from the value in the JSON response (e.g., "123" is a `string`, 123 is an `integer`).

5.  **Enhance Schemas with Nullable Info:**
    - Parse the database schema from the `.sql` file to identify which columns are `NOT NULL`.
    - Update the schemas generated in the previous step by adding `nullable: true` or `nullable: false` to each property based on the database schema.

6.  **Generate Final OpenAPI Specification:**
    - Create the final OpenAPI 3.0 specification.
    - Use the enhanced schemas from the previous step.
    - Include all endpoints from the Postman collection (GET, POST, PUT, DELETE).
    - Add standard parameters (`limit`, `offset`, `sort`, `filter`) to all `GET` collection endpoints.

7.  **Deliver Final Files:**
    - Provide the final, validated `openapi.yaml`.
    - Provide the final, validated `openapi.json`.
    - Provide a summary of the work done (e.g., how many endpoints were tested, how many schemas were generated).

**Required Files to Attach:**

1.  `VetmanagerCollection.postman_collection.json` (The exported Postman collection)
2.  `vm_devtr6_dump_data.sql.gz` (The gzipped SQL database dump)

Thank you!
```
## How to host Swagger API documentation with GitHub Pages
[<img alt="The blog of Peter Evans: How to Host Swagger Documentation With Github Pages" title="View blog post" src="https://peterevans.dev/img/blog-published-badge.svg">](https://peterevans.dev/posts/how-to-host-swagger-docs-with-github-pages/)

This repository is a template for using the [Swagger UI](https://github.com/swagger-api/swagger-ui) to dynamically generate beautiful documentation for your API and host it for free with GitHub Pages.

The template will periodically auto-update the Swagger UI dependency and create a pull request. See the [GitHub Actions workflow here](.github/workflows/update-swagger.yml).

The example API specification used by this repository can be seen hosted at [https://peter-evans.github.io/swagger-github-pages](https://peter-evans.github.io/swagger-github-pages/).

## Steps to use this template

1. Click the `Use this template` button above to create a new repository from this template.

2. Go to the settings for your repository at `https://github.com/{github-username}/{repository-name}/settings` and enable GitHub Pages.

    ![Headers](/screenshots/swagger-github-pages.png?raw=true)
    
3. Browse to the Swagger documentation at `https://{github-username}.github.io/{repository-name}/`.


## Steps to manually configure in your own repository

1. Download the latest stable release of the Swagger UI [here](https://github.com/swagger-api/swagger-ui/releases).

2. Extract the contents and copy the "dist" directory to the root of your repository.

3. Move the file "index.html" from the directory "dist" to the root of your repository.
    ```
    mv dist/index.html .
    ```
    
4. Copy the YAML specification file for your API to the root of your repository.

5. Edit [dist/swagger-initializer.js](dist/swagger-initializer.js) and change the `url` property to reference your local YAML file. 
    ```javascript
        window.ui = SwaggerUIBundle({
            url: "swagger.yaml",
        ...
    ```
    Then fix any references to files in the "dist" directory.
    ```html
    ...
    <link rel="stylesheet" type="text/css" href="dist/swagger-ui.css" >
    <link rel="icon" type="image/png" href="dist/favicon-32x32.png" sizes="32x32" />
    <link rel="icon" type="image/png" href="dist/favicon-16x16.png" sizes="16x16" />    
    ...
    <script src="dist/swagger-ui-bundle.js"> </script>
    <script src="dist/swagger-ui-standalone-preset.js"> </script>    
    ...
    ```
    
6. Go to the settings for your repository at `https://github.com/{github-username}/{repository-name}/settings` and enable GitHub Pages.

    ![Headers](/screenshots/swagger-github-pages.png?raw=true)
    
7. Browse to the Swagger documentation at `https://{github-username}.github.io/{repository-name}/`.

   The example API specification used by this repository can be seen hosted at [https://peter-evans.github.io/swagger-github-pages](https://peter-evans.github.io/swagger-github-pages/).
