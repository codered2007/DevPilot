from app.services.dependency_analysis import (
    parse_cargo_toml,
    parse_go_mod,
    parse_package_json,
    parse_pom_xml,
    parse_pyproject_toml,
    parse_requirements_txt,
)


def test_package_json():
    result = parse_package_json(
        """
        {
          "dependencies": {
            "react": "^19.2.7",
            "react-dom": "^19.2.7"
          },
          "devDependencies": {
            "vite": "^7.3.6"
          }
        }
        """
    )

    assert len(result) == 3

    names = {
        dependency["name"]
        for dependency in result
    }

    assert names == {
        "react",
        "react-dom",
        "vite",
    }


def test_requirements_txt():
    result = parse_requirements_txt(
        """
        fastapi==0.115.0
        httpx>=0.28
        pydantic~=2.10
        """
    )

    assert len(result) == 3
    assert result[0]["name"] == "fastapi"
    assert result[0]["version"] == "==0.115.0"
    assert result[0]["ecosystem"] == "pip"


def test_pyproject_toml():
    result = parse_pyproject_toml(
        """
        [project]
        dependencies = [
            "fastapi>=0.115",
            "httpx>=0.28"
        ]

        [project.optional-dependencies]
        dev = [
            "pytest>=8"
        ]
        """
    )

    assert len(result) == 3

    names = {
        dependency["name"]
        for dependency in result
    }

    assert names == {
        "fastapi",
        "httpx",
        "pytest",
    }


def test_pom_xml():
    result = parse_pom_xml(
        """
        <project>
          <dependencies>
            <dependency>
              <groupId>org.springframework</groupId>
              <artifactId>spring-core</artifactId>
              <version>6.2.0</version>
            </dependency>
            <dependency>
              <groupId>org.junit</groupId>
              <artifactId>junit</artifactId>
              <version>5.11.0</version>
              <scope>test</scope>
            </dependency>
          </dependencies>
        </project>
        """
    )

    assert len(result) == 2
    assert result[0]["name"] == (
        "org.springframework:spring-core"
    )
    assert result[0]["ecosystem"] == "maven"
    assert result[1]["scope"] == "test"


def test_go_mod():
    result = parse_go_mod(
        """
        module example.com/devpilot

        go 1.24

        require (
            github.com/foo/bar v1.2.3
            github.com/baz/qux v2.0.1
        )
        """
    )

    assert len(result) == 2

    names = {
        dependency["name"]
        for dependency in result
    }

    assert names == {
        "github.com/foo/bar",
        "github.com/baz/qux",
    }


def test_cargo_toml():
    result = parse_cargo_toml(
        """
        [dependencies]
        serde = "1.0"
        tokio = { version = "1.42", features = ["full"] }

        [dev-dependencies]
        pretty_assertions = "1.4"
        """
    )

    assert len(result) == 3

    names = {
        dependency["name"]
        for dependency in result
    }

    assert names == {
        "serde",
        "tokio",
        "pretty_assertions",
    }

    tokio = next(
        dependency
        for dependency in result
        if dependency["name"] == "tokio"
    )

    assert tokio["version"] == "1.42"