import asyncio
import importlib

import pytest
from fastapi import HTTPException


CASES = [
    (
        "app.api.architecture_analysis",
        "architecture_analysis",
        ["analyze_repository_architecture"],
    ),
    (
        "app.api.dependency_analysis",
        "dependency_analysis",
        ["analyze_repository_dependencies"],
    ),
    (
        "app.api.security_analysis",
        "security_analysis",
        [
            "analyze_repository_dependencies",
            "analyze_repository_security",
        ],
    ),
    (
        "app.api.summary",
        "repository_summary",
        ["summarize_repository"],
    ),
]


@pytest.mark.parametrize(
    "module_name,route_name,service_names",
    CASES,
)
def test_analysis_routes_reject_inaccessible_repository(
    monkeypatch, module_name, route_name, service_names
):
    module = importlib.import_module(module_name)

    async def reject_access(owner, repo, token):
        assert owner == "private-owner"
        assert repo == "private-repo"
        assert token == "user-token"
        raise HTTPException(status_code=403, detail="Forbidden")

    async def unexpected_service(*args, **kwargs):
        pytest.fail("Analysis service ran without repository authorization.")

    monkeypatch.setattr(
        module, "get_accessible_repository", reject_access
    )

    for service_name in service_names:
        monkeypatch.setattr(
            module, service_name, unexpected_service
        )

    route = getattr(module, route_name)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            route(
                owner="private-owner",
                repo="private-repo",
                session={"access_token": "user-token"},
            )
        )

    assert exc.value.status_code == 403
