from __future__ import annotations

from typing import Any

import httpx


OSV_QUERY_BATCH_URL = (
    "https://api.osv.dev/v1/querybatch"
)


ECOSYSTEM_MAP = {
    "npm": "npm",
    "pip": "PyPI",
    "maven": "Maven",
    "go": "Go",
    "cargo": "crates.io",
}


SEVERITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "MODERATE": 2,
    "LOW": 1,
    "UNKNOWN": 0,
}


SEVERITY_ALIASES = {
    "MODERATE": "MEDIUM",
}


def normalize_ecosystem(
    ecosystem: str,
) -> str | None:
    return ECOSYSTEM_MAP.get(
        ecosystem.lower()
    )


def normalize_severity(
    vulnerability: dict[str, Any],
) -> str:
    database_specific = vulnerability.get(
        "database_specific",
        {},
    )

    if isinstance(
        database_specific,
        dict,
    ):
        value = database_specific.get(
            "severity"
        )

        if isinstance(value, str):
            normalized = value.upper()

            return SEVERITY_ALIASES.get(
                normalized,
                normalized,
            )

    severities = vulnerability.get(
        "severity",
        [],
    )

    if isinstance(
        severities,
        list,
    ):
        for severity in severities:
            if not isinstance(
                severity,
                dict,
            ):
                continue

            score = severity.get(
                "score"
            )

            if not isinstance(
                score,
                str,
            ):
                continue

            # We deliberately don't derive a
            # severity label from a CVSS vector.
            # OSV's database_specific severity,
            # when present, is preferred.
            continue

    return "UNKNOWN"


def extract_aliases(
    vulnerability: dict[str, Any],
) -> list[str]:
    aliases = vulnerability.get(
        "aliases",
        [],
    )

    if not isinstance(
        aliases,
        list,
    ):
        return []

    return sorted(
        {
            str(alias)
            for alias in aliases
            if alias
        }
    )


def extract_fixed_versions(
    vulnerability: dict[str, Any],
) -> list[str]:
    fixed_versions: set[str] = set()

    affected = vulnerability.get(
        "affected",
        [],
    )

    if not isinstance(
        affected,
        list,
    ):
        return []

    for affected_item in affected:
        if not isinstance(
            affected_item,
            dict,
        ):
            continue

        ranges = affected_item.get(
            "ranges",
            [],
        )

        if not isinstance(
            ranges,
            list,
        ):
            continue

        for range_item in ranges:
            if not isinstance(
                range_item,
                dict,
            ):
                continue

            events = range_item.get(
                "events",
                [],
            )

            if not isinstance(
                events,
                list,
            ):
                continue

            for event in events:
                if not isinstance(
                    event,
                    dict,
                ):
                    continue

                fixed = event.get(
                    "fixed"
                )

                if fixed:
                    fixed_versions.add(
                        str(fixed)
                    )

    return sorted(
        fixed_versions
    )


def extract_references(
    vulnerability: dict[str, Any],
) -> list[str]:
    references = vulnerability.get(
        "references",
        [],
    )

    if not isinstance(
        references,
        list,
    ):
        return []

    urls: set[str] = set()

    for reference in references:
        if not isinstance(
            reference,
            dict,
        ):
            continue

        url = reference.get(
            "url"
        )

        if url:
            urls.add(str(url))

    return sorted(urls)


def build_query(
    dependency: dict[str, Any],
) -> dict[str, Any] | None:
    ecosystem = normalize_ecosystem(
        dependency.get(
            "ecosystem",
            "",
        )
    )

    name = dependency.get(
        "name",
        "",
    ).strip()

    declared_version = dependency.get(
        "version",
        "",
    ).strip()

    resolved_version = dependency.get(
        "resolved_version",
        "",
    ).strip()

    if not ecosystem or not name:
        return None

    # Prefer the lockfile-resolved version because it represents
    # the actual installed package version. This avoids treating
    # a semver range such as "^7.1.7" as an exact version.
    version = (
        resolved_version
        if resolved_version
        else declared_version
    )

    if not version:
        return None

    # Without a resolved version, normalize exact pins
    # such as ==1.2.3 and =1.2.3.
    if not resolved_version:
        if version.startswith("=="):
            version = version[2:].strip()
        elif version.startswith("="):
            version = version[1:].strip()

        if not version:
            return None

        # Genuine version ranges cannot safely be mapped
        # to one exact OSV version.
        if version.startswith((
            "^",
            "~",
            ">",
            "<",
        )):
            return None

    return {
        "package": {
            "name": name,
            "ecosystem": ecosystem,
        },
        "version": version,
    }


def parse_vulnerability(
    vulnerability: dict[str, Any],
    dependency: dict[str, Any],
) -> dict[str, Any]:
    vulnerability_id = vulnerability.get(
        "id",
        "UNKNOWN",
    )

    return {
        "id": str(
            vulnerability_id
        ),
        "aliases": extract_aliases(
            vulnerability
        ),
        "package": dependency.get(
            "name",
            "",
        ),
        "version": dependency.get(
            "version",
            "",
        ),
        "resolved_version": dependency.get(
            "resolved_version",
            "",
        ),
        "ecosystem": dependency.get(
            "ecosystem",
            "",
        ),
        "manifest": dependency.get(
            "manifest",
            "",
        ),
        "scope": dependency.get(
            "scope",
            "",
        ),
        "severity": normalize_severity(
            vulnerability
        ),
        "summary": vulnerability.get(
            "summary",
            "",
        ),
        "details": vulnerability.get(
            "details",
            "",
        ),
        "fixed_versions": (
            extract_fixed_versions(
                vulnerability
            )
        ),
        "references": extract_references(
            vulnerability
        ),
        "published": vulnerability.get(
            "published"
        ),
        "modified": vulnerability.get(
            "modified"
        ),
    }


def deduplicate_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: dict[
        tuple[str, str, str, str],
        dict[str, Any],
    ] = {}

    for finding in findings:
        key = (
            finding.get(
                "id",
                "",
            ),
            finding.get(
                "package",
                "",
            ).lower(),
            finding.get(
                "version",
                "",
            ),
            finding.get(
                "manifest",
                "",
            ),
        )

        unique[key] = finding

    return sorted(
        unique.values(),
        key=lambda item: (
            -SEVERITY_ORDER.get(
                item.get(
                    "severity",
                    "UNKNOWN",
                ),
                0,
            ),
            item.get(
                "package",
                "",
            ).lower(),
            item.get(
                "id",
                "",
            ),
        ),
    )


def build_summary(
    findings: list[dict[str, Any]],
) -> dict[str, int]:
    summary = {
        "total": len(findings),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "unknown": 0,
    }

    for finding in findings:
        severity = finding.get(
            "severity",
            "UNKNOWN",
        ).lower()

        key = (
            severity
            if severity in summary
            else "unknown"
        )

        summary[key] += 1

    return summary


async def analyze_repository_security(
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    queries: list[
        dict[str, Any]
    ] = []

    query_dependencies: list[
        dict[str, Any]
    ] = []

    for dependency in dependencies:
        query = build_query(
            dependency
        )

        if query is None:
            continue

        queries.append(query)

        query_dependencies.append(
            dependency
        )

    if not queries:
        return {
            "findings": [],
            "summary": build_summary([]),
            "scanned_dependencies": 0,
            "skipped_dependencies": len(
                dependencies
            ),
        }

    payload = {
        "queries": queries
    }

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:
        response = await client.post(
            OSV_QUERY_BATCH_URL,
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

    results = data.get(
        "results",
        [],
    )

    findings: list[
        dict[str, Any]
    ] = []

    for index, result in enumerate(
        results
    ):
        if index >= len(
            query_dependencies
        ):
            break

        dependency = query_dependencies[
            index
        ]

        vulnerabilities = result.get(
            "vulns",
            [],
        )

        if not isinstance(
            vulnerabilities,
            list,
        ):
            continue

        for vulnerability in vulnerabilities:
            if not isinstance(
                vulnerability,
                dict,
            ):
                continue

            findings.append(
                parse_vulnerability(
                    vulnerability,
                    dependency,
                )
            )

    findings = deduplicate_findings(
        findings
    )

    return {
        "findings": findings,
        "summary": build_summary(
            findings
        ),
        "scanned_dependencies": len(
            query_dependencies
        ),
        "skipped_dependencies": (
            len(dependencies)
            - len(query_dependencies)
        ),
    }