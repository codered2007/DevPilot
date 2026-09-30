import base64
import json
import re
import tomllib
import xml.etree.ElementTree as ET

from app.services.github_service import (
    get_file_content,
    get_repository_tree,
)


MANIFEST_NAMES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "go.mod",
    "cargo.toml",
}

LOCKFILE_NAMES = {
    "package-lock.json",
}

def get_manifest_type(path: str) -> str | None:
    filename = path.rsplit("/", 1)[-1].lower()

    if filename == "package.json":
        return "npm"

    if filename == "requirements.txt":
        return "pip"

    if filename == "pyproject.toml":
        return "python"

    if filename == "pom.xml":
        return "maven"

    if filename == "go.mod":
        return "go"

    if filename == "cargo.toml":
        return "cargo"

    return None


def decode_github_content(file_data: dict) -> str:
    raw_content = file_data.get("content", "")

    if not raw_content:
        return ""

    try:
        decoded = base64.b64decode(
            raw_content
        )

        return decoded.decode(
            "utf-8",
            errors="replace",
        )

    except (ValueError, TypeError):
        return ""


def parse_package_json(
    content: str,
) -> list[dict]:
    try:
        data = json.loads(content)
    except (
        json.JSONDecodeError,
        TypeError,
    ):
        return []

    dependencies = []

    for section in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        values = data.get(section, {})

        if not isinstance(values, dict):
            continue

        for name, version in values.items():
            dependencies.append(
                {
                    "name": name,
                    "version": str(version),
                    "scope": section,
                    "ecosystem": "npm",
                }
            )

    return dependencies
def parse_package_lock_json(
    content: str,
) -> dict[str, str]:
    try:
        data = json.loads(content)
    except (
        json.JSONDecodeError,
        TypeError,
    ):
        return {}

    if data.get("lockfileVersion") != 3:
        return {}

    packages = data.get(
        "packages",
        {},
    )

    if not isinstance(
        packages,
        dict,
    ):
        return {}

    resolved_versions: dict[str, str] = {}

    for package_path, package_data in packages.items():
        if not isinstance(
            package_data,
            dict,
        ):
            continue

        if not package_path.startswith(
            "node_modules/"
        ):
            continue

        package_name = package_path[
            len("node_modules/"):
        ]

        if (
            "/node_modules/"
            in package_name
        ):
            continue

        version = package_data.get(
            "version"
        )

        if not isinstance(
            version,
            str,
        ):
            continue

        resolved_versions[
            package_name
        ] = version

    return resolved_versions

def parse_requirements_txt(
    content: str,
) -> list[dict]:
    dependencies = []

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if line.startswith(
            (
                "-r ",
                "--requirement ",
            )
        ):
            continue

        if line.startswith(
            (
                "-c ",
                "--constraint ",
            )
        ):
            continue

        line = line.split(
            " #",
            1,
        )[0].strip()

        match = re.match(
            r"^([A-Za-z0-9_.-]+)"
            r"\s*"
            r"((?:==|>=|<=|~=|!=|>|<).*)?$",
            line,
        )

        if not match:
            continue

        name = match.group(1)
        version = (
            match.group(2) or ""
        ).strip()

        dependencies.append(
            {
                "name": name,
                "version": version,
                "scope": "runtime",
                "ecosystem": "pip",
            }
        )

    return dependencies


def parse_pyproject_toml(
    content: str,
) -> list[dict]:
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return []

    dependencies = []

    project = data.get(
        "project",
        {},
    )

    if isinstance(project, dict):
        for dependency in project.get(
            "dependencies",
            [],
        ):
            parsed = parse_python_dependency(
                dependency,
                "runtime",
            )

            if parsed:
                dependencies.append(parsed)

        optional_dependencies = project.get(
            "optional-dependencies",
            {},
        )

        if isinstance(
            optional_dependencies,
            dict,
        ):
            for group, values in (
                optional_dependencies.items()
            ):
                if not isinstance(
                    values,
                    list,
                ):
                    continue

                for dependency in values:
                    parsed = parse_python_dependency(
                        dependency,
                        group,
                    )

                    if parsed:
                        dependencies.append(parsed)

    poetry = (
        data.get("tool", {})
        .get("poetry", {})
    )

    if isinstance(
        poetry,
        dict,
    ):
        poetry_dependencies = poetry.get(
            "dependencies",
            {},
        )

        if isinstance(
            poetry_dependencies,
            dict,
        ):
            for name, value in (
                poetry_dependencies.items()
            ):
                if name.lower() == "python":
                    continue

                dependencies.append(
                    {
                        "name": name,
                        "version": (
                            normalize_python_version(
                                value
                            )
                        ),
                        "scope": "runtime",
                        "ecosystem": "pip",
                    }
                )

        poetry_groups = poetry.get(
            "group",
            {},
        )

        if isinstance(
            poetry_groups,
            dict,
        ):
            for group_name, group_data in (
                poetry_groups.items()
            ):
                if not isinstance(
                    group_data,
                    dict,
                ):
                    continue

                group_dependencies = (
                    group_data.get(
                        "dependencies",
                        {},
                    )
                )

                if not isinstance(
                    group_dependencies,
                    dict,
                ):
                    continue

                for name, value in (
                    group_dependencies.items()
                ):
                    dependencies.append(
                        {
                            "name": name,
                            "version": (
                                normalize_python_version(
                                    value
                                )
                            ),
                            "scope": group_name,
                            "ecosystem": "pip",
                        }
                    )

    return deduplicate_dependencies(
        dependencies
    )


def parse_python_dependency(
    dependency: str,
    scope: str,
) -> dict | None:
    if not isinstance(
        dependency,
        str,
    ):
        return None

    match = re.match(
        r"^\s*"
        r"([A-Za-z0-9_.-]+)"
        r"\s*(.*)$",
        dependency,
    )

    if not match:
        return None

    name = match.group(1)
    version = match.group(2).strip()

    return {
        "name": name,
        "version": version,
        "scope": scope,
        "ecosystem": "pip",
    }


def normalize_python_version(
    value,
) -> str:
    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        version = value.get(
            "version"
        )

        if isinstance(
            version,
            str,
        ):
            return version

        return ""

    return str(value)


def parse_pom_xml(
    content: str,
) -> list[dict]:
    try:
        root = ET.fromstring(
            content
        )
    except ET.ParseError:
        return []

    dependencies = []

    namespace_match = re.match(
        r"\{([^}]+)\}",
        root.tag,
    )

    namespace = (
        namespace_match.group(1)
        if namespace_match
        else None
    )

    if namespace:
        dependency_path = (
            ".//{"
            + namespace
            + "}dependency"
        )

        group_tag = (
            "{"
            + namespace
            + "}groupId"
        )

        artifact_tag = (
            "{"
            + namespace
            + "}artifactId"
        )

        version_tag = (
            "{"
            + namespace
            + "}version"
        )

        scope_tag = (
            "{"
            + namespace
            + "}scope"
        )

    else:
        dependency_path = ".//dependency"
        group_tag = "groupId"
        artifact_tag = "artifactId"
        version_tag = "version"
        scope_tag = "scope"

    for dependency in root.findall(
        dependency_path
    ):
        group_id = dependency.findtext(
            group_tag,
            default="",
        ).strip()

        artifact_id = dependency.findtext(
            artifact_tag,
            default="",
        ).strip()

        version = dependency.findtext(
            version_tag,
            default="",
        ).strip()

        scope = dependency.findtext(
            scope_tag,
            default="runtime",
        ).strip()

        if not artifact_id:
            continue

        name = (
            f"{group_id}:{artifact_id}"
            if group_id
            else artifact_id
        )

        dependencies.append(
            {
                "name": name,
                "version": version,
                "scope": scope,
                "ecosystem": "maven",
            }
        )

    return dependencies


def parse_go_mod(
    content: str,
) -> list[dict]:
    dependencies = []

    in_require_block = False

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("//"):
            continue

        if line.startswith(
            "require ("
        ):
            in_require_block = True
            continue

        if (
            in_require_block
            and line == ")"
        ):
            in_require_block = False
            continue

        if line.startswith(
            "require "
        ):
            line = line[
                len("require "):
            ].strip()

        if (
            not in_require_block
            and not line.startswith(
                "require"
            )
        ):
            continue

        parts = line.split()

        if len(parts) < 2:
            continue

        name = parts[0]
        version = parts[1]

        if name == "require":
            continue

        dependencies.append(
            {
                "name": name,
                "version": version,
                "scope": "runtime",
                "ecosystem": "go",
            }
        )

    return dependencies


def parse_cargo_toml(
    content: str,
) -> list[dict]:
    try:
        data = tomllib.loads(
            content
        )
    except tomllib.TOMLDecodeError:
        return []

    dependencies = []

    sections = [
        (
            "dependencies",
            "runtime",
        ),
        (
            "dev-dependencies",
            "dev",
        ),
        (
            "build-dependencies",
            "build",
        ),
    ]

    for section_name, scope in sections:
        values = data.get(
            section_name,
            {},
        )

        if not isinstance(
            values,
            dict,
        ):
            continue

        for name, value in values.items():
            dependencies.append(
                {
                    "name": name,
                    "version": (
                        normalize_cargo_version(
                            value
                        )
                    ),
                    "scope": scope,
                    "ecosystem": "cargo",
                }
            )

    return dependencies


def normalize_cargo_version(
    value,
) -> str:
    if isinstance(
        value,
        str,
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        version = value.get(
            "version"
        )

        if isinstance(
            version,
            str,
        ):
            return version

        return ""

    return str(value)


def deduplicate_dependencies(
    dependencies: list[dict],
) -> list[dict]:
    seen = set()
    result = []

    for dependency in dependencies:
        key = (
            dependency.get(
                "ecosystem",
                "",
            ),
            dependency.get(
                "name",
                "",
            ).lower(),
            dependency.get(
                "scope",
                "",
            ),
            dependency.get(
                "manifest",
                "",
            ),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(
            dependency
        )

    return result


def parse_manifest(
    manifest_type: str,
    content: str,
) -> list[dict]:
    if manifest_type == "npm":
        return parse_package_json(
            content
        )

    if manifest_type == "pip":
        return parse_requirements_txt(
            content
        )

    if manifest_type == "python":
        return parse_pyproject_toml(
            content
        )

    if manifest_type == "maven":
        return parse_pom_xml(
            content
        )

    if manifest_type == "go":
        return parse_go_mod(
            content
        )

    if manifest_type == "cargo":
        return parse_cargo_toml(
            content
        )

    return []


async def analyze_repository_dependencies(
    owner: str,
    repo: str,
) -> dict:
    tree = await get_repository_tree(
        owner,
        repo,
    )

    if not tree:
        return {
            "manifests": [],
            "dependencies": [],
            "summary": {
                "manifest_count": 0,
                "dependency_count": 0,
                "ecosystems": [],
            },
        }

    manifests = []

    for item in tree.get(
        "tree",
        [],
    ):
        if item.get(
            "type"
        ) != "blob":
            continue

        path = item.get(
            "path",
            "",
        )

        filename = path.rsplit(
            "/",
            1,
        )[-1].lower()

        if filename not in MANIFEST_NAMES:
            continue

        manifest_type = get_manifest_type(
            path
        )

        if not manifest_type:
            continue

        manifests.append(
            {
                "path": path,
                "ecosystem": manifest_type,
            }
        )

    manifests.sort(
        key=lambda item: item[
            "path"
        ].lower()
    )
    lockfiles = {}

    for item in tree.get(
        "tree",
        [],
    ):
        if item.get(
            "type"
        ) != "blob":
            continue

        path = item.get(
            "path",
            "",
        )

        filename = path.rsplit(
            "/",
            1,
        )[-1].lower()

        if filename not in LOCKFILE_NAMES:
            continue

        file_data = await get_file_content(
            owner,
            repo,
            path,
        )

        if not file_data:
            continue

        content = decode_github_content(
            file_data
        )

        if not content:
            continue

        if filename == "package-lock.json":
            lockfiles[path] = (
                parse_package_lock_json(
                    content
                )
            )

    dependencies = []

    for manifest in manifests:
        file_data = await get_file_content(
            owner,
            repo,
            manifest["path"],
        )

        if not file_data:
            continue

        content = decode_github_content(
            file_data
        )

        if not content:
            continue

        parsed = parse_manifest(
            manifest["ecosystem"],
            content,
        )

        for dependency in parsed:
            dependency["manifest"] = (
                manifest["path"]
            )

            if (
                manifest["ecosystem"]
                == "npm"
            ):
                manifest_directory = (
                    manifest["path"].rsplit(
                        "/",
                        1,
                    )[0]
                    if "/"
                    in manifest["path"]
                    else ""
                )

                lockfile_path = (
                    f"{manifest_directory}/package-lock.json"
                    if manifest_directory
                    else "package-lock.json"
                )

                resolved_versions = (
                    lockfiles.get(
                        lockfile_path,
                        {},
                    )
                )

                resolved_version = (
                    resolved_versions.get(
                        dependency.get(
                            "name",
                            "",
                        )
                    )
                )

                if resolved_version:
                    dependency[
                        "resolved_version"
                    ] = resolved_version

        dependencies.extend(
            parsed
        )

    dependencies = (
        deduplicate_dependencies(
            dependencies
        )
    )

    dependencies.sort(
        key=lambda item: (
            item.get(
                "ecosystem",
                "",
            ),
            item.get(
                "name",
                "",
            ).lower(),
            item.get(
                "scope",
                "",
            ),
            item.get(
                "manifest",
                "",
            ).lower(),
        )
    )

    return {
        "manifests": manifests,
        "dependencies": dependencies,
        "summary": {
            "manifest_count": len(
                manifests
            ),
            "dependency_count": len(
                dependencies
            ),
            "ecosystems": sorted(
                {
                    manifest[
                        "ecosystem"
                    ]
                    for manifest in manifests
                }
            ),
        },
    }