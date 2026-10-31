import pytest
from pydantic import ValidationError

from app.schemas.apply_code import ApplyCodeRequest
from app.schemas.code_actions import CodeActionRequest
from app.schemas.explanation import ExplainRequest


@pytest.mark.parametrize(
    "schema",
    [ApplyCodeRequest, CodeActionRequest, ExplainRequest],
)
@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "src/../../secret",
        "/etc/passwd",
        r"..\secret",
        "src\\..\\secret",
        "src//main.py",
        "./main.py",
        "src/./main.py",
        "src/\x00main.py",
        "",
    ],
)
def test_rejects_unsafe_file_paths(schema, path):
    data = {
        "owner": "example",
        "repo": "demo",
        "file_path": path,
        "code": "print('hello')",
    }

    if schema is not ExplainRequest:
        data["action"] = "fix"

    with pytest.raises(ValidationError):
        schema(**data)


@pytest.mark.parametrize(
    "schema",
    [ApplyCodeRequest, CodeActionRequest, ExplainRequest],
)
@pytest.mark.parametrize(
    "path",
    [
        "main.py",
        "src/main.py",
        "src/components/App.tsx",
    ],
)
def test_accepts_safe_file_paths(schema, path):
    data = {
        "owner": "example",
        "repo": "demo",
        "file_path": path,
        "code": "print('hello')",
    }

    if schema is not ExplainRequest:
        data["action"] = "fix"

    request = schema(**data)
    assert request.file_path == path
