# Vetmanager OpenAPI reconciliation

Generated: 2026-06-15T15:20:29Z

## Source counts

- openapi_operations: 136
- mcp_openapi_operations: 126
- mcp_postman_operations: 126
- postman_public_operations: 136
- extjs_route_candidates: 430
- db_nullable_tables: 146

## Matrix status

- confirmed: 136
- extjs_only_candidate: 336

## Documented elsewhere but missing from OpenAPI

- None

## ExtJS-only route candidates

- `DELETE /rest/api/admissionJournal/{id}`: extjs_default_rest
- `DELETE /rest/api/anonymousClient/{id}`: extjs_default_rest
- `DELETE /rest/api/apiError/{id}`: extjs_default_rest
- `DELETE /rest/api/breed/{id}`: extjs_default_rest
- `DELETE /rest/api/cassa/{id}`: extjs_default_rest
- `DELETE /rest/api/cassaclose/{id}`: extjs_default_rest
- `DELETE /rest/api/cassarashod/{id}`: extjs_default_rest
- `DELETE /rest/api/clientDiscountCard/{id}`: extjs_default_rest
- `DELETE /rest/api/clientPhone/{id}`: extjs_default_rest
- `DELETE /rest/api/clinics/{id}`: extjs_default_rest
- `DELETE /rest/api/clinicsToClients/{id}`: extjs_default_rest
- `DELETE /rest/api/clinicsToDocuments/{id}`: extjs_default_rest
- `DELETE /rest/api/closingOfInvoices/{id}`: extjs_default_rest
- `DELETE /rest/api/comboManualItem/{id}`: extjs_default_rest
- `DELETE /rest/api/comboManualName/{id}`: extjs_default_rest
- `DELETE /rest/api/departmentToDocument/{id}`: extjs_default_rest
- `DELETE /rest/api/departments/{id}`: extjs_default_rest
- `DELETE /rest/api/diagnoses/{id}`: extjs_default_rest
- `DELETE /rest/api/discountCardType/{id}`: extjs_default_rest
- `DELETE /rest/api/doctorsResponsible/{id}`: extjs_default_rest
- `DELETE /rest/api/documentNumber/{id}`: extjs_default_rest
- `DELETE /rest/api/failedHook/{id}`: extjs_default_rest
- `DELETE /rest/api/fiscalRegister/{id}`: extjs_default_rest
- `DELETE /rest/api/fiscalRegisterData/{id}`: extjs_default_rest
- `DELETE /rest/api/fiscalTaxSystems/{id}`: extjs_default_rest
- `DELETE /rest/api/goodGroup/{id}`: extjs_default_rest
- `DELETE /rest/api/goodSaleParam/{id}`: extjs_default_rest
- `DELETE /rest/api/hospital/{id}`: extjs_default_rest
- `DELETE /rest/api/hospitalBlock/{id}`: extjs_default_rest
- `DELETE /rest/api/invoice/{id}`: extjs_default_rest
- `DELETE /rest/api/invoiceDocument/{id}`: extjs_default_rest
- `DELETE /rest/api/lastTime/{id}`: extjs_default_rest
- `DELETE /rest/api/medicalCards/{id}`: extjs_default_rest
- `DELETE /rest/api/messages/{id}`: extjs_default_rest
- `DELETE /rest/api/mobileAccess/{id}`: extjs_default_rest
- `DELETE /rest/api/partyAccount/{id}`: extjs_default_rest
- `DELETE /rest/api/partyAccountDoc/{id}`: extjs_default_rest
- `DELETE /rest/api/payment/{id}`: extjs_default_rest
- `DELETE /rest/api/petType/{id}`: extjs_default_rest
- `DELETE /rest/api/ping/{id}`: extjs_default_rest
- `DELETE /rest/api/properties/{id}`: extjs_default_rest
- `DELETE /rest/api/providerLabRequests/{id}`: extjs_default_rest
- `DELETE /rest/api/proxy/{id}`: extjs_default_rest
- `DELETE /rest/api/report/{id}`: extjs_default_rest
- `DELETE /rest/api/reportAiJobs/{id}`: extjs_default_rest
- `DELETE /rest/api/role/{id}`: extjs_default_rest
- `DELETE /rest/api/servicePrice/{id}`: extjs_default_rest
- `DELETE /rest/api/storeDocument/{id}`: extjs_default_rest
- `DELETE /rest/api/storeDocumentOperation/{id}`: extjs_default_rest
- `DELETE /rest/api/stores/{id}`: extjs_default_rest
- `DELETE /rest/api/suppliers/{id}`: extjs_default_rest
- `DELETE /rest/api/tariff/{id}`: extjs_default_rest
- `DELETE /rest/api/timesheet/{id}`: extjs_default_rest
- `DELETE /rest/api/timesheetTypes/{id}`: extjs_default_rest
- `DELETE /rest/api/unit/{id}`: extjs_default_rest
- `DELETE /rest/api/user/{id}`: extjs_default_rest
- `DELETE /rest/api/userAccess/{id}`: extjs_default_rest
- `DELETE /rest/api/userCalls/{id}`: extjs_default_rest
- `DELETE /rest/api/userConfig/{id}`: extjs_default_rest
- `DELETE /rest/api/userToken/{id}`: extjs_default_rest
- `DELETE /rest/api/vmLink/{id}`: extjs_default_rest
- `DELETE /rest/api/webHook/{id}`: extjs_default_rest
- `DELETE /rest/api/{controller}`: extjs_explicit_route
- `DELETE /rest/api/{controller}/{id}`: extjs_explicit_route
- `GET /rest/api/admissionJournal`: extjs_default_rest
- `GET /rest/api/admissionJournal/{id}`: extjs_default_rest
- `GET /rest/api/apiError`: extjs_default_rest
- `GET /rest/api/apiError/{id}`: extjs_default_rest
- `GET /rest/api/cassa/casses-data`: extjs_custom_rest
- `GET /rest/api/client/client-contacts-data`: extjs_custom_rest
- `GET /rest/api/client/clients-match-data`: extjs_custom_rest
- `GET /rest/api/client/clients-search-data`: extjs_custom_rest
- `GET /rest/api/clientDiscountCard`: extjs_default_rest
- `GET /rest/api/clientDiscountCard/{id}`: extjs_default_rest
- `GET /rest/api/clientPhone`: extjs_default_rest
- `GET /rest/api/clientPhone/{id}`: extjs_default_rest
- `GET /rest/api/clinicsToClients`: extjs_default_rest
- `GET /rest/api/clinicsToClients/{id}`: extjs_default_rest
- `GET /rest/api/clinicsToDocuments`: extjs_default_rest
- `GET /rest/api/clinicsToDocuments/{id}`: extjs_default_rest
- `GET /rest/api/comboManualItem`: extjs_default_rest
- `GET /rest/api/comboManualItem/reasons-of-visit-data`: extjs_custom_rest
- `GET /rest/api/comboManualItem/{id}`: extjs_default_rest
- `GET /rest/api/comboManualName`: extjs_default_rest
- `GET /rest/api/comboManualName/{id}`: extjs_default_rest
- `GET /rest/api/departmentToDocument`: extjs_default_rest
- `GET /rest/api/departmentToDocument/{id}`: extjs_default_rest
- `GET /rest/api/departments`: extjs_default_rest
- `GET /rest/api/departments/{id}`: extjs_default_rest
- `GET /rest/api/diagnoses`: extjs_default_rest
- `GET /rest/api/diagnoses/{id}`: extjs_default_rest
- `GET /rest/api/discountCardType`: extjs_default_rest
- `GET /rest/api/discountCardType/{id}`: extjs_default_rest
- `GET /rest/api/doctorsResponsible`: extjs_default_rest
- `GET /rest/api/doctorsResponsible/{id}`: extjs_default_rest
- `GET /rest/api/documentNumber`: extjs_default_rest
- `GET /rest/api/documentNumber/{id}`: extjs_default_rest
- `GET /rest/api/failedHook`: extjs_default_rest
- `GET /rest/api/failedHook/{id}`: extjs_default_rest
- `GET /rest/api/fiscalRegister`: extjs_default_rest
- `GET /rest/api/fiscalRegister/evotor-fiscal-register`: extjs_custom_rest
- `GET /rest/api/fiscalRegister/linked-fiscal-register-to-user`: extjs_custom_rest
- `GET /rest/api/fiscalRegister/{id}`: extjs_default_rest
- `GET /rest/api/good/categories-products`: extjs_custom_rest
- `GET /rest/api/good/check-product-data`: extjs_custom_rest
- `GET /rest/api/good/good-by-barcode`: extjs_custom_rest
- `GET /rest/api/good/good-sale-price-by-id-sale-param-id-clinic-id`: extjs_custom_rest
- `GET /rest/api/good/good-sets-data`: extjs_custom_rest
- `GET /rest/api/good/goods-categories`: extjs_custom_rest
- `GET /rest/api/good/goods-vaccines`: extjs_custom_rest
- `GET /rest/api/good/products-data-for-invoice`: extjs_custom_rest
- `GET /rest/api/good/simple-products-for-editor`: extjs_custom_rest
- `GET /rest/api/good/stock-balances-for-product`: extjs_custom_rest
- `GET /rest/api/goodGroup`: extjs_default_rest
- `GET /rest/api/goodSaleParam/{id}`: extjs_default_rest
- `GET /rest/api/hospitalBlock`: extjs_default_rest
- `GET /rest/api/hospitalBlock/{id}`: extjs_default_rest
- `GET /rest/api/lastTime`: extjs_default_rest
- `GET /rest/api/lastTime/{id}`: extjs_default_rest
- `GET /rest/api/medicalCards`: extjs_default_rest
- `GET /rest/api/medicalCards/all-diagnoses`: extjs_custom_rest
- `GET /rest/api/medicalCards/medcards-text-templates`: extjs_custom_rest
- `GET /rest/api/medicalCards/medicalcard-item-by-client`: extjs_custom_rest
- `GET /rest/api/medicalCards/medicalcards-data-by-client`: extjs_custom_rest
- `GET /rest/api/medicalCards/vaccinations`: extjs_custom_rest
- `GET /rest/api/medicalCards/{id}`: extjs_default_rest
- `GET /rest/api/messages`: extjs_default_rest
- `GET /rest/api/messages/{id}`: extjs_default_rest
- `GET /rest/api/mobileAccess`: extjs_default_rest
- `GET /rest/api/mobileAccess/check-authorization-data`: extjs_custom_rest
- `GET /rest/api/mobileAccess/{id}`: extjs_default_rest
- `GET /rest/api/partyAccount`: extjs_default_rest
- `GET /rest/api/partyAccount/party-info-by-invoice-document-id`: extjs_custom_rest
- `GET /rest/api/partyAccount/{id}`: extjs_default_rest
- `GET /rest/api/partyAccountDoc`: extjs_default_rest
- `GET /rest/api/partyAccountDoc/{id}`: extjs_default_rest
- `GET /rest/api/ping`: extjs_default_rest
- `GET /rest/api/ping/{id}`: extjs_default_rest
- `GET /rest/api/properties/{id}`: extjs_default_rest
- `GET /rest/api/providerLabRequests`: extjs_default_rest
- `GET /rest/api/providerLabRequests/{id}`: extjs_default_rest
- `GET /rest/api/proxy`: extjs_default_rest
- `GET /rest/api/proxy/{id}`: extjs_default_rest
- `GET /rest/api/report`: extjs_default_rest
- `GET /rest/api/report/report-file`: extjs_custom_rest
- `GET /rest/api/report/start-report`: extjs_custom_rest
- `GET /rest/api/report/{id}`: extjs_default_rest
- `GET /rest/api/reportAiJobs`: extjs_default_rest
- `GET /rest/api/reportAiJobs/{id}`: extjs_default_rest
- `GET /rest/api/servicePrice`: extjs_default_rest
- ... 186 more

## OpenAPI-only entries

- None
