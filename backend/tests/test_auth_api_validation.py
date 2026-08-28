from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.errors import request_validation_error_handler
from app.api.v1.auth import get_auth_service, router


def test_register_rejects_client_supplied_admin_role_with_error_contract() -> None:
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.include_router(router)
    app.dependency_overrides[get_auth_service] = lambda: object()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Attacker",
            "email": "attacker@example.com",
            "password": "strong-password",
            "role": "ADMIN",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
