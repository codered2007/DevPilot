
import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from app.api import repositories


def make_github_error(
    status_code: int,
    *,
    headers: dict | None = None,
    body: dict | None = None,
) -> httpx.HTTPStatusError:
    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/test-owner/test-repo",
    )
    response = httpx.Response(
        status_code,
        headers=headers,
        json=body or {},
        request=request,
    )

    return httpx.HTTPStatusError(
        "GitHub request failed",
        request=request,
        response=response,
    )


@pytest.mark.parametrize(
    ("status_code", "headers", "body"),
    [
        (429, {}, {"message": "Too many requests"}),
        (
            403,
            {"Retry-After": "60"},
            {"message": "Forbidden"},
        ),
        (
            403,
            {"X-RateLimit-Remaining": "0"},
            {"message": "API rate limit exceeded"},
        ),
        (
            403,
            {},
            {"message": "You have exceeded a secondary rate limit"},
        ),
    ],
)
def test_rate_limits_map_to_429(
    status_code,
    headers,
    body,
):
    error = make_github_error(
        status_code,
        headers=headers,
        body=body,
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 429
    assert "rate limit" in exc_info.value.detail.lower()


def test_retry_after_header_is_preserved():
    error = make_github_error(
        429,
        headers={"Retry-After": "30"},
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["Retry-After"] == "30"


def test_invalid_github_token_maps_to_401():
    error = make_github_error(
        401,
        body={"message": "Bad credentials"},
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 401
    assert "authentication failed" in exc_info.value.detail.lower()


def test_ordinary_permission_denial_maps_to_403():
    error = make_github_error(
        403,
        body={"message": "Resource access is forbidden"},
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 403


def test_not_found_maps_to_404():
    error = make_github_error(
        404,
        body={"message": "Not Found"},
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 404


def test_unexpected_github_error_maps_to_safe_502():
    secret_body = "sensitive-response-content"
    error = make_github_error(
        500,
        body={"message": secret_body},
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_http_error(error)

    assert exc_info.value.status_code == 502
    assert secret_body not in exc_info.value.detail


def test_network_error_maps_to_safe_502():
    request = httpx.Request(
        "GET",
        "https://api.github.com/repos/test-owner/test-repo",
    )
    error = httpx.ConnectError(
        "connection failed with sensitive details",
        request=request,
    )

    with pytest.raises(HTTPException) as exc_info:
        repositories._raise_github_network_error(error)

    assert exc_info.value.status_code == 502
    assert "sensitive details" not in exc_info.value.detail


def test_accessible_repository_forwards_user_token(monkeypatch):
    async def run_test():
        mock_get_repository = AsyncMock(
            return_value={
                "full_name": "test-owner/test-repo",
            }
        )
        monkeypatch.setattr(
            repositories,
            "get_repository",
            mock_get_repository,
        )

        result = await repositories.get_accessible_repository(
            "test-owner",
            "test-repo",
            "user-specific-token",
        )

        assert result["full_name"] == "test-owner/test-repo"
        mock_get_repository.assert_awaited_once_with(
            "test-owner",
            "test-repo",
            token="user-specific-token",
        )

    asyncio.run(run_test())


def test_missing_token_is_rejected_before_github_call(monkeypatch):
    async def run_test():
        mock_get_repository = AsyncMock()
        monkeypatch.setattr(
            repositories,
            "get_repository",
            mock_get_repository,
        )

        with pytest.raises(HTTPException) as exc_info:
            await repositories.get_accessible_repository(
                "test-owner",
                "test-repo",
                "",
            )

        assert exc_info.value.status_code == 401
        mock_get_repository.assert_not_awaited()

    asyncio.run(run_test())
