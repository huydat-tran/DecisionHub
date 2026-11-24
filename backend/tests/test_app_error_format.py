"""Smoke test: xác nhận app thật dùng format lỗi chuẩn (không cần MySQL)."""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient

from app.main import app


class TestRealAppErrorFormat(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_unknown_route_uses_standard_error_shape(self) -> None:
        response = self.client.get("/api/v1/does-not-exist")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(
            set(body.keys()),
            {"success", "message", "data", "error_code", "errors", "path"},
        )
        self.assertFalse(body["success"])
        self.assertEqual(body["error_code"], "NOT_FOUND")
        self.assertEqual(body["path"], "/api/v1/does-not-exist")

    def test_validation_error_uses_standard_error_shape(self) -> None:
        response = self.client.post("/auth/login", json={"email": "x"})
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["message"], "Dữ liệu đầu vào không hợp lệ")
        self.assertEqual(body["error_code"], "VALIDATION_ERROR")
        self.assertTrue(body["errors"])
        self.assertIn("field", body["errors"][0])
        self.assertIn("message", body["errors"][0])


if __name__ == "__main__":
    unittest.main()
