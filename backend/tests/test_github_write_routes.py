
import asyncio
import importlib
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException


apply_code_module = importlib.import_module("app.api.apply_code")
pull_request_module = importlib.import_module("app.api.pull_request")


def run(coro):
    return asyncio.run(coro)


def github_http_error(status_code, headers=None, json=None):
    request = httpx.Request(
        "POST",
        "https://api.github.com/test",
    )
    response = httpx.Response(
        status_code,
        headers=headers,
        json=json,
        request=request,
    )
    return httpx.HTTPStatusError(
        "GitHub request failed",
        request=request,
        response=response,
    )


def network_error():
    request = httpx.Request(
        "POST",
        "https://api.github.com/test",
    )
    return httpx.ConnectError(
        "Connection failed",
        request=request,
    )


def apply_request():
    return SimpleNamespace(
        owner="test-owner",
        repo="test-repo",
        file_path="src/example.py",
        action="update",
        code="print('updated')",
    )


def pull_request_request():
    return SimpleNamespace(
        owner="test-owner",
        repo="test-repo",
        title="Test pull request",
        body="Test description",
        head="devpilot/test",
        base="main",
    )


def configure_access(monkeypatch, module):
    async def accessible_repository(owner, repo, token):
        assert owner == "test-owner"
        assert repo == "test-repo"
        assert token == "user-token"
        return {"full_name": "test-owner/test-repo"}

    monkeypatch.setattr(
        module,
        "get_accessible_repository",
        accessible_repository,
    )


def test_apply_code_rejects_missing_token():
    with pytest.raises(HTTPException) as exc:
        run(
            apply_code_module.apply_code(
                apply_request(),
                session={},
            )
        )

    assert exc.value.status_code == 401


def test_pull_request_rejects_missing_token():
    with pytest.raises(HTTPException) as exc:
        run(
            pull_request_module.create_pull_request_route(
                pull_request_request(),
                session={},
            )
        )

    assert exc.value.status_code == 401


@pytest.mark.parametrize(
    "status_code,headers,json_body,expected_status",
    [
        (401, {}, {"message": "Bad credentials"}, 401),
        (
            403,
            {"X-RateLimit-Remaining": "0"},
            {"message": "API rate limit exceeded"},
            429,
        ),
        (403, {}, {"message": "Forbidden"}, 403),
        (404, {}, {"message": "Not Found"}, 404),
        (500, {}, {"message": "Internal error"}, 502),
    ],
)
def test_apply_code_maps_github_http_errors(
    monkeypatch,
    status_code,
    headers,
    json_body,
    expected_status,
):
    configure_access(monkeypatch, apply_code_module)

    async def fail(*args, **kwargs):
        raise github_http_error(
            status_code,
            headers=headers,
            json=json_body,
        )

    monkeypatch.setattr(
        apply_code_module,
        "get_default_branch",
        fail,
    )

    with pytest.raises(HTTPException) as exc:
        run(
            apply_code_module.apply_code(
                apply_request(),
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == expected_status


@pytest.mark.parametrize(
    "status_code,headers,json_body,expected_status",
    [
        (401, {}, {"message": "Bad credentials"}, 401),
        (
            403,
            {"X-RateLimit-Remaining": "0"},
            {"message": "API rate limit exceeded"},
            429,
        ),
        (403, {}, {"message": "Forbidden"}, 403),
        (404, {}, {"message": "Not Found"}, 404),
        (500, {}, {"message": "Internal error"}, 502),
    ],
)
def test_pull_request_maps_github_http_errors(
    monkeypatch,
    status_code,
    headers,
    json_body,
    expected_status,
):
    configure_access(monkeypatch, pull_request_module)

    async def fail(*args, **kwargs):
        raise github_http_error(
            status_code,
            headers=headers,
            json=json_body,
        )

    monkeypatch.setattr(
        pull_request_module,
        "create_pull_request",
        fail,
    )

    with pytest.raises(HTTPException) as exc:
        run(
            pull_request_module.create_pull_request_route(
                pull_request_request(),
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == expected_status


def test_apply_code_maps_network_errors(monkeypatch):
    configure_access(monkeypatch, apply_code_module)

    async def fail(*args, **kwargs):
        raise network_error()

    monkeypatch.setattr(
        apply_code_module,
        "get_default_branch",
        fail,
    )

    with pytest.raises(HTTPException) as exc:
        run(
            apply_code_module.apply_code(
                apply_request(),
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == 502


def test_pull_request_maps_network_errors(monkeypatch):
    configure_access(monkeypatch, pull_request_module)

    async def fail(*args, **kwargs):
        raise network_error()

    monkeypatch.setattr(
        pull_request_module,
        "create_pull_request",
        fail,
    )

    with pytest.raises(HTTPException) as exc:
        run(
            pull_request_module.create_pull_request_route(
                pull_request_request(),
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == 502

def test_apply_code_success(monkeypatch):
    configure_access(monkeypatch, apply_code_module)

    async def default_branch(*args, **kwargs):
        return "main"

    async def branch_sha(*args, **kwargs):
        return "base-sha"

    async def create_branch(*args, **kwargs):
        return "refs/heads/devpilot/update-example.py"

    async def update_file(*args, **kwargs):
        return {
            "branch": "devpilot/update-example.py",
            "commit_sha": "commit-sha",
            "commit_url": "https://github.com/test-owner/test-repo/commit/commit-sha",
        }

    monkeypatch.setattr(
        apply_code_module, "get_default_branch", default_branch
    )
    monkeypatch.setattr(
        apply_code_module, "get_branch_sha", branch_sha
    )
    monkeypatch.setattr(
        apply_code_module, "create_branch", create_branch
    )
    monkeypatch.setattr(
        apply_code_module, "update_file_on_branch", update_file
    )

    result = run(
        apply_code_module.apply_code(
            apply_request(),
            session={"access_token": "user-token"},
        )
    )

    assert result["message"] == "Code applied successfully."
    assert result["owner"] == "test-owner"
    assert result["repo"] == "test-repo"
    assert result["base_branch"] == "main"
    assert result["commit_sha"] == "commit-sha"


def test_pull_request_success(monkeypatch):
    configure_access(monkeypatch, pull_request_module)

    async def create_pr(*args, **kwargs):
        return {
            "number": 42,
            "title": "Test pull request",
            "url": "https://github.com/test-owner/test-repo/pull/42",
            "state": "open",
            "head": "devpilot/test",
            "base": "main",
        }

    monkeypatch.setattr(
        pull_request_module, "create_pull_request", create_pr
    )

    result = run(
        pull_request_module.create_pull_request_route(
            pull_request_request(),
            session={"access_token": "user-token"},
        )
    )

    assert result["message"] == "Pull Request created successfully."
    assert result["number"] == 42
    assert result["state"] == "open"
    assert result["head"] == "devpilot/test"
    assert result["base"] == "main"


@pytest.mark.parametrize(
    "module,route,request_factory",
    [
        (
            apply_code_module,
            apply_code_module.apply_code,
            apply_request,
        ),
        (
            pull_request_module,
            pull_request_module.create_pull_request_route,
            pull_request_request,
        ),
    ],
)
def test_repository_access_failure_prevents_write(
    monkeypatch, module, route, request_factory
):
    async def reject_access(owner, repo, token):
        raise HTTPException(status_code=403, detail="Forbidden")

    async def unexpected_write(*args, **kwargs):
        pytest.fail("Write operation must not run without repository access.")

    monkeypatch.setattr(
        module, "get_accessible_repository", reject_access
    )

    if module is apply_code_module:
        monkeypatch.setattr(
            module, "get_default_branch", unexpected_write
        )
    else:
        monkeypatch.setattr(
            module, "create_pull_request", unexpected_write
        )

    with pytest.raises(HTTPException) as exc:
        run(
            route(
                request_factory(),
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == 403
