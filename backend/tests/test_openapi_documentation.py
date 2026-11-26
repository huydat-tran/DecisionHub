"""Kiểm tra tài liệu OpenAPI của 3 API auth/users có đầy đủ mô tả và ví dụ."""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app


class TestOpenApiDocumentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.spec = app.openapi()

    def _operation(self, path: str, method: str) -> dict:
        return self.spec["paths"][path][method]

    def _example(self, operation: dict, status_code: str) -> dict:
        content = operation["responses"][status_code]["content"]["application/json"]
        return content["example"]

    def _request_example(self, operation: dict) -> dict:
        content = operation["requestBody"]["content"]["application/json"]
        examples = content["examples"]
        return next(iter(examples.values()))["value"]

    def test_register_has_summary_description_and_request_example(self) -> None:
        operation = self._operation("/auth/register", "post")
        self.assertTrue(operation["summary"])
        self.assertTrue(operation["description"])
        request_example = self._request_example(operation)
        self.assertEqual(
            set(request_example.keys()), {"username", "email", "password"}
        )

    def test_register_declares_error_responses(self) -> None:
        operation = self._operation("/auth/register", "post")
        self.assertIn("201", operation["responses"])
        for status_code in ("409", "422", "500"):
            self.assertIn(status_code, operation["responses"])
            example = self._example(operation, status_code)
            self.assertFalse(example["success"])
            self.assertEqual(example["error_code"], {
                "409": "CONFLICT",
                "422": "VALIDATION_ERROR",
                "500": "INTERNAL_SERVER_ERROR",
            }[status_code])
            self.assertEqual(example["path"], "/auth/register")

    def test_login_has_summary_description_and_request_example(self) -> None:
        operation = self._operation("/auth/login", "post")
        self.assertTrue(operation["summary"])
        self.assertTrue(operation["description"])
        request_example = self._request_example(operation)
        self.assertEqual(set(request_example.keys()), {"email", "password"})

    def test_login_declares_error_responses(self) -> None:
        operation = self._operation("/auth/login", "post")
        self.assertIn("200", operation["responses"])
        for status_code in ("401", "422"):
            self.assertIn(status_code, operation["responses"])
            example = self._example(operation, status_code)
            self.assertFalse(example["success"])
            self.assertEqual(example["path"], "/auth/login")
        self.assertEqual(
            self._example(operation, "401")["error_code"], "UNAUTHORIZED"
        )

    def test_login_response_example_contains_access_token(self) -> None:
        operation = self._operation("/auth/login", "post")
        schema_ref = operation["responses"]["200"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        schema_name = schema_ref.rsplit("/", 1)[-1]
        example = self.spec["components"]["schemas"][schema_name]["example"]
        self.assertIn("access_token", example["data"])
        self.assertEqual(example["data"]["token_type"], "bearer")

    def test_users_me_requires_bearer_security(self) -> None:
        operation = self._operation("/users/me", "get")
        self.assertTrue(operation["summary"])
        self.assertTrue(operation["description"])
        self.assertIn({"HTTPBearer": []}, operation["security"])

    def test_users_me_declares_unauthorized_response(self) -> None:
        operation = self._operation("/users/me", "get")
        self.assertIn("200", operation["responses"])
        self.assertIn("401", operation["responses"])
        example = self._example(operation, "401")
        self.assertEqual(example["error_code"], "UNAUTHORIZED")
        self.assertEqual(example["path"], "/users/me")

    def test_error_response_schema_is_documented(self) -> None:
        schema = self.spec["components"]["schemas"]["ErrorResponse"]
        self.assertEqual(
            set(schema["required"]), {"message", "error_code", "path"}
        )


if __name__ == "__main__":
    unittest.main()
