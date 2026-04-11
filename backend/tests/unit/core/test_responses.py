"""
Unit tests for src/core/responses.py

Verifies that all three response helpers produce the correct JSON structure
and HTTP status codes required by Architecture Rule #14:
  success: {success, data, message}
  paginated: {success, data, pagination}
  error: {success, error, code}
"""
import json

from fastapi.responses import JSONResponse

from src.core.responses import success_response, paginated_response, error_response


def _body(response: JSONResponse) -> dict:
    """Decode JSONResponse body to a plain dict."""
    return json.loads(response.body)


class TestSuccessResponse:
    def test_returns_json_response(self):
        resp = success_response(data={"id": "1"})
        assert isinstance(resp, JSONResponse)

    def test_default_status_code_is_200(self):
        resp = success_response(data={})
        assert resp.status_code == 200

    def test_custom_status_code(self):
        resp = success_response(data={}, status_code=201)
        assert resp.status_code == 201

    def test_success_field_is_true(self):
        body = _body(success_response(data={"id": "1"}, message="OK"))
        assert body["success"] is True

    def test_data_field_is_present(self):
        body = _body(success_response(data={"id": "1"}, message="OK"))
        assert body["data"] == {"id": "1"}

    def test_message_field_is_present(self):
        body = _body(success_response(data={"id": "1"}, message="OK"))
        assert body["message"] == "OK"

    def test_default_message_is_OK(self):
        body = _body(success_response(data={}))
        assert body["message"] == "OK"

    def test_no_error_field_present(self):
        body = _body(success_response(data={}))
        assert "error" not in body

    def test_list_data_preserved(self):
        body = _body(success_response(data=[1, 2, 3]))
        assert body["data"] == [1, 2, 3]

    def test_none_data_preserved(self):
        body = _body(success_response(data=None))
        assert body["data"] is None

    def test_nested_data_preserved(self):
        nested = {"user": {"id": "abc", "roles": ["admin"]}}
        body = _body(success_response(data=nested))
        assert body["data"]["user"]["roles"] == ["admin"]


class TestPaginatedResponse:
    def test_returns_json_response(self):
        resp = paginated_response(data=[], page=1, limit=20, total=0)
        assert isinstance(resp, JSONResponse)

    def test_status_code_is_200(self):
        resp = paginated_response(data=[], page=1, limit=20, total=0)
        assert resp.status_code == 200

    def test_success_field_is_true(self):
        body = _body(paginated_response(data=[1, 2, 3], page=1, limit=20, total=3))
        assert body["success"] is True

    def test_data_field_is_preserved(self):
        body = _body(paginated_response(data=[1, 2, 3], page=1, limit=20, total=3))
        assert body["data"] == [1, 2, 3]

    def test_pagination_key_present(self):
        body = _body(paginated_response(data=[1, 2, 3], page=1, limit=20, total=3))
        assert "pagination" in body

    def test_pagination_contains_page(self):
        body = _body(paginated_response(data=[], page=2, limit=10, total=25))
        assert body["pagination"]["page"] == 2

    def test_pagination_contains_limit(self):
        body = _body(paginated_response(data=[], page=2, limit=10, total=25))
        assert body["pagination"]["limit"] == 10

    def test_pagination_contains_total(self):
        body = _body(paginated_response(data=[], page=2, limit=10, total=25))
        assert body["pagination"]["total"] == 25

    def test_pagination_total_pages_calculated_correctly(self):
        # 25 items, 10 per page → 3 pages
        body = _body(paginated_response(data=[], page=1, limit=10, total=25))
        assert body["pagination"]["total_pages"] == 3

    def test_pagination_total_pages_exact_division(self):
        # 20 items, 10 per page → 2 pages (no ceiling needed)
        body = _body(paginated_response(data=[], page=1, limit=10, total=20))
        assert body["pagination"]["total_pages"] == 2

    def test_pagination_total_pages_zero_total(self):
        body = _body(paginated_response(data=[], page=1, limit=20, total=0))
        assert body["pagination"]["total_pages"] == 0

    def test_pagination_total_pages_single_item(self):
        body = _body(paginated_response(data=[], page=1, limit=20, total=1))
        assert body["pagination"]["total_pages"] == 1

    def test_no_message_field_present(self):
        # Paginated responses don't include a message field
        body = _body(paginated_response(data=[], page=1, limit=20, total=0))
        assert "message" not in body

    def test_no_error_field_present(self):
        body = _body(paginated_response(data=[], page=1, limit=20, total=0))
        assert "error" not in body


class TestErrorResponse:
    def test_returns_json_response(self):
        resp = error_response("not found", "NOT_FOUND", 404)
        assert isinstance(resp, JSONResponse)

    def test_status_code_is_set(self):
        resp = error_response("not found", "NOT_FOUND", 404)
        assert resp.status_code == 404

    def test_success_field_is_false(self):
        body = _body(error_response("not found", "NOT_FOUND", 404))
        assert body["success"] is False

    def test_error_field_contains_message(self):
        body = _body(error_response("not found", "NOT_FOUND", 404))
        assert body["error"] == "not found"

    def test_code_field_is_present(self):
        body = _body(error_response("not found", "NOT_FOUND", 404))
        assert body["code"] == "NOT_FOUND"

    def test_no_data_field_present(self):
        body = _body(error_response("bad request", "BAD_REQUEST", 400))
        assert "data" not in body

    def test_details_omitted_when_none(self):
        body = _body(error_response("err", "CODE", 400))
        assert "details" not in body

    def test_details_omitted_when_empty_list(self):
        body = _body(error_response("err", "CODE", 400, details=[]))
        assert "details" not in body

    def test_details_included_when_provided(self):
        body = _body(error_response("err", "CODE", 400, details=["field required"]))
        assert body["details"] == ["field required"]

    def test_409_conflict_response(self):
        resp = error_response("Email already registered", "CONFLICT", 409)
        assert resp.status_code == 409
        body = _body(resp)
        assert body["success"] is False
        assert body["code"] == "CONFLICT"

    def test_422_validation_error_response(self):
        resp = error_response("Validation failed", "VALIDATION_ERROR", 422)
        assert resp.status_code == 422

    def test_503_service_unavailable_response(self):
        resp = error_response("Database unreachable", "DB_ERROR", 503)
        assert resp.status_code == 503
