"""Kiểm thử cơ chế chuẩn hóa response lỗi của DecisionHub.

Dùng một app FastAPI độc lập để không phụ thuộc Database.
"""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.common.exceptions import (
    DecisionHubException,
    ResourceNotFoundException,
    register_exception_handlers,
)
from app.common.responses import success_response


class Payload(BaseModel):
    name: str


def build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/400")
    def boom_400():
        raise HTTPException(status_code=400, detail="Yêu cầu không hợp lệ.")

    @app.get("/boom/401")
    def boom_401():
        raise HTTPException(status_code=401, detail="Chưa xác thực.")

    @app.get("/boom/403")
    def boom_403():
        raise HTTPException(status_code=403, detail="Không có quyền.")

    @app.get("/boom/404")
    def boom_404():
        raise HTTPException(status_code=404, detail="Không tìm thấy.")

    @app.get("/boom/422")
    def boom_422():
        raise HTTPException(status_code=422, detail="Không xử lý được.")

    @app.get("/boom/500")
    def boom_500():
        raise DecisionHubException(message="Lỗi nội bộ.", status_code=500)

    @app.get("/boom/unexpected")
    def boom_unexpected():
        raise RuntimeError("chi tiết không nên lộ ra")

    @app.get("/boom/not-found-exc")
    def boom_not_found_exc():
        raise ResourceNotFoundException("Món ăn", 99)

    @app.get("/boom/hub")
    def boom_hub():
        raise DecisionHubException(
            message="Email đã được đăng ký.",
            status_code=409,
            data={"field": "email"},
            error_code="CONFLICT",
        )

    @app.post("/validate")
    def validate(payload: Payload):
        return success_response({"name": payload.name})

    @app.get("/ok")
    def ok():
        return success_response({"status": "ok"})

    return app


ERROR_KEYS = {"success", "message", "data", "error_code", "errors", "path"}


class TestErrorResponseFormat(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_app(), raise_server_exceptions=False)

    def assert_error_shape(self, response, expected_status: int) -> dict:
        self.assertEqual(response.status_code, expected_status)
        body = response.json()
        self.assertEqual(set(body.keys()), ERROR_KEYS)
        self.assertFalse(body["success"])
        self.assertIsInstance(body["message"], str)
        self.assertIn("error_code", body)
        self.assertIsInstance(body["path"], str)
        return body

    def test_http_400(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/400"), 400)
        self.assertEqual(body["message"], "Yêu cầu không hợp lệ.")
        self.assertEqual(body["error_code"], "BAD_REQUEST")
        self.assertIsNone(body["data"])
        self.assertIsNone(body["errors"])

    def test_http_401(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/401"), 401)
        self.assertEqual(body["error_code"], "UNAUTHORIZED")

    def test_http_403(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/403"), 403)
        self.assertEqual(body["error_code"], "FORBIDDEN")

    def test_http_404(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/404"), 404)
        self.assertEqual(body["error_code"], "NOT_FOUND")

    def test_http_422(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/422"), 422)
        self.assertEqual(body["error_code"], "VALIDATION_ERROR")

    def test_http_500(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/500"), 500)
        self.assertEqual(body["error_code"], "INTERNAL_SERVER_ERROR")

    def test_unexpected_exception_returns_500_without_details(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/unexpected"), 500)
        self.assertEqual(body["error_code"], "INTERNAL_SERVER_ERROR")
        self.assertNotIn("chi tiết không nên lộ ra", response_text(body))

    def test_request_validation_error(self) -> None:
        response = self.client.post("/validate", json={"name": 123})
        body = self.assert_error_shape(response, 422)
        self.assertEqual(body["message"], "Dữ liệu đầu vào không hợp lệ")
        self.assertEqual(body["error_code"], "VALIDATION_ERROR")
        self.assertIsInstance(body["errors"], list)
        self.assertTrue(body["errors"])
        self.assertIn("field", body["errors"][0])
        self.assertIn("message", body["errors"][0])

    def test_resource_not_found_exception(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/not-found-exc"), 404)
        self.assertEqual(body["error_code"], "RESOURCE_NOT_FOUND")
        self.assertEqual(body["data"], {"resource": "Món ăn", "id": 99})
        self.assertEqual(body["path"], "/boom/not-found-exc")

    def test_custom_exception_keeps_data_and_error_code(self) -> None:
        body = self.assert_error_shape(self.client.get("/boom/hub"), 409)
        self.assertEqual(body["error_code"], "CONFLICT")
        self.assertEqual(body["data"], {"field": "email"})
        self.assertIsNone(body["errors"])

    def test_unknown_route_returns_standard_404(self) -> None:
        body = self.assert_error_shape(self.client.get("/khong-ton-tai"), 404)
        self.assertEqual(body["error_code"], "NOT_FOUND")
        self.assertEqual(body["path"], "/khong-ton-tai")

    def test_success_response_unchanged(self) -> None:
        response = self.client.get("/ok")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"success": True, "message": "OK", "data": {"status": "ok"}},
        )


def response_text(body: dict) -> str:
    return str(body)


if __name__ == "__main__":
    unittest.main()
