import pytest

from app.services.dependency_analysis import (
    parse_package_json,
    parse_package_lock_json,
    parse_requirements_txt,
    parse_pyproject_toml,
    parse_pom_xml,
    parse_go_mod,
    parse_cargo_toml,
)


def test_parse_package_json():
    content = """
    {
      "dependencies": {
        "react": "^19.0.0"
      },
      "devDependencies": {
        "vite": "^7.1.7"
      }
    }
    """

    result = parse_package_json(content)

    assert len(result) == 2
    assert {
        "name": "react",
        "version": "^19.0.0",
        "scope": "dependencies",
        "ecosystem": "npm",
    } in result
    assert {
        "name": "vite",
        "version": "^7.1.7",
        "scope": "devDependencies",
        "ecosystem": "npm",
    } in result


def test_parse_requirements_txt():
    content = """
    fastapi==0.115.0
    httpx>=0.27.0
    # comment
    """

    result = parse_requirements_txt(content)

    assert len(result) == 2
    assert result[0]["name"] == "fastapi"
    assert result[0]["version"] == "==0.115.0"
    assert result[1]["name"] == "httpx"
    assert result[1]["version"] == ">=0.27.0"


def test_parse_pyproject_toml():
    content = """
    [project]
    dependencies = [
      "fastapi>=0.115.0",
      "httpx==0.27.2"
    ]
    """

    result = parse_pyproject_toml(content)

    assert len(result) == 2
    assert result[0]["name"] == "fastapi"
    assert result[1]["name"] == "httpx"


def test_parse_pom_xml():
    content = """
    <project xmlns="http://maven.apache.org/POM/4.0.0">
      <dependencies>
        <dependency>
          <groupId>org.example</groupId>
          <artifactId>demo</artifactId>
          <version>1.2.3</version>
        </dependency>
      </dependencies>
    </project>
    """

    result = parse_pom_xml(content)

    assert len(result) == 1
    assert result[0]["name"] == "org.example:demo"
    assert result[0]["version"] == "1.2.3"
    assert result[0]["ecosystem"] == "maven"


def test_parse_go_mod():
    content = """
    module example.com/demo

    require (
        github.com/example/foo v1.2.3
        github.com/example/bar v2.0.0
    )
    """

    result = parse_go_mod(content)

    assert len(result) == 2
    assert result[0]["name"] == "github.com/example/foo"
    assert result[0]["version"] == "v1.2.3"
    assert result[1]["name"] == "github.com/example/bar"
    assert result[1]["version"] == "v2.0.0"


def test_parse_cargo_toml():
    content = """
    [dependencies]
    serde = "1.0"

    [dev-dependencies]
    tokio = "1.0"
    """

    result = parse_cargo_toml(content)

    assert len(result) == 2
    assert result[0]["name"] == "serde"
    assert result[0]["version"] == "1.0"
    assert result[1]["name"] == "tokio"
    assert result[1]["version"] == "1.0"


def test_parse_package_lock_json_v3():
    content = """
    {
      "lockfileVersion": 3,
      "packages": {
        "": {
          "name": "DevPilot"
        },
        "node_modules/vite": {
          "version": "7.3.6"
        },
        "node_modules/react": {
          "version": "19.2.8"
        },
        "node_modules/@scope/example": {
          "version": "1.2.3"
        },
        "node_modules/foo/node_modules/bar": {
          "version": "9.9.9"
        }
      }
    }
    """

    result = parse_package_lock_json(content)

    assert result["vite"] == "7.3.6"
    assert result["react"] == "19.2.8"
    assert result["@scope/example"] == "1.2.3"
    assert "foo/node_modules/bar" not in result


def test_parse_package_lock_json_unsupported_version():
    content = """
    {
      "lockfileVersion": 2,
      "packages": {
        "node_modules/vite": {
          "version": "7.3.6"
        }
      }
    }
    """

    result = parse_package_lock_json(content)

    assert result == {}


def test_parse_package_lock_json_invalid_json():
    content = """
    {
      "lockfileVersion": 3,
      "packages":
    """

    result = parse_package_lock_json(content)

    assert result == {}
