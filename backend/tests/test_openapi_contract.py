from app.main import app


EXPECTED_PATHS = {
    "/api/v1/facilities",
    "/api/v1/facilities/nearby",
    "/api/v1/facilities/{facility_id}",
    "/api/v1/reports",
    "/api/v1/reports/{report_id}",
    "/api/v1/reports/{report_id}/confirm",
    "/api/v1/map/reports",
    "/api/v1/map/facilities",
    "/api/v1/map/hotspots",
    "/api/v1/sync/report-status",
    "/api/v1/admin/reports",
    "/api/v1/admin/reports/{report_id}",
    "/api/v1/admin/reports/{report_id}/status",
    "/api/v1/admin/facilities",
    "/api/v1/admin/facilities/{facility_id}",
    "/api/v1/admin/knowledge",
    "/api/v1/admin/knowledge/{knowledge_id}",
}


def test_all_backend_contract_paths_are_in_openapi() -> None:
    schema = app.openapi()
    assert EXPECTED_PATHS <= set(schema["paths"])


def test_non_public_modules_declare_bearer_auth() -> None:
    schema = app.openapi()
    for path in EXPECTED_PATHS:
        for operation in schema["paths"][path].values():
            assert operation.get("security") == [{"HTTPBearer": []}]
    assert schema["paths"]["/health"]["get"].get("security") is None
    assert schema["paths"]["/api/v1/categories"]["get"].get("security") is None
