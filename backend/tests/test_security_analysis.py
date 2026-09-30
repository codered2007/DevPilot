from app.services.security_analysis import (
    build_summary,
    deduplicate_findings,
    extract_aliases,
    extract_fixed_versions,
    normalize_ecosystem,
    normalize_severity,
    parse_vulnerability,
)


def test_normalize_ecosystem():
    assert normalize_ecosystem("npm") == "npm"
    assert normalize_ecosystem("pip") == "PyPI"
    assert normalize_ecosystem("maven") == "Maven"
    assert normalize_ecosystem("go") == "Go"
    assert normalize_ecosystem("cargo") == "crates.io"
    assert normalize_ecosystem("unknown") is None


def test_normalize_severity():
    vulnerability = {
        "database_specific": {
            "severity": "HIGH"
        }
    }

    assert (
        normalize_severity(vulnerability)
        == "HIGH"
    )


def test_normalize_severity_unknown():
    vulnerability = {}

    assert (
        normalize_severity(vulnerability)
        == "UNKNOWN"
    )


def test_extract_aliases():
    vulnerability = {
        "aliases": [
            "CVE-2026-1234",
            "GHSA-xxxx-yyyy-zzzz",
        ]
    }

    assert extract_aliases(
        vulnerability
    ) == [
        "CVE-2026-1234",
        "GHSA-xxxx-yyyy-zzzz",
    ]


def test_extract_fixed_versions():
    vulnerability = {
        "affected": [
            {
                "ranges": [
                    {
                        "events": [
                            {
                                "introduced": "0"
                            },
                            {
                                "fixed": "2.4.1"
                            },
                        ]
                    }
                ]
            }
        ]
    }

    assert extract_fixed_versions(
        vulnerability
    ) == ["2.4.1"]


def test_parse_vulnerability():
    vulnerability = {
        "id": "GHSA-test-1234",
        "aliases": [
            "CVE-2026-1234"
        ],
        "summary": "Test vulnerability",
        "details": "Test details",
        "database_specific": {
            "severity": "HIGH"
        },
        "affected": [
            {
                "ranges": [
                    {
                        "events": [
                            {
                                "introduced": "0"
                            },
                            {
                                "fixed": "2.0.0"
                            },
                        ]
                    }
                ]
            }
        ],
        "references": [
            {
                "type": "ADVISORY",
                "url": (
                    "https://example.com/advisory"
                ),
            }
        ],
    }

    dependency = {
        "name": "example-package",
        "version": "1.0.0",
        "ecosystem": "npm",
        "manifest": "package.json",
        "scope": "runtime",
    }

    result = parse_vulnerability(
        vulnerability,
        dependency,
    )

    assert result["id"] == "GHSA-test-1234"
    assert result["package"] == "example-package"
    assert result["version"] == "1.0.0"
    assert result["ecosystem"] == "npm"
    assert result["manifest"] == "package.json"
    assert result["scope"] == "runtime"
    assert result["severity"] == "HIGH"
    assert result["aliases"] == [
        "CVE-2026-1234"
    ]
    assert result["fixed_versions"] == [
        "2.0.0"
    ]
    assert result["references"] == [
        "https://example.com/advisory"
    ]


def test_deduplicate_findings():
    finding = {
        "id": "GHSA-test",
        "package": "example-package",
        "version": "1.0.0",
        "manifest": "package.json",
        "severity": "HIGH",
    }

    duplicate = dict(finding)

    result = deduplicate_findings(
        [finding, duplicate]
    )

    assert len(result) == 1


def test_deduplicate_keeps_different_manifests():
    first = {
        "id": "GHSA-test",
        "package": "example-package",
        "version": "1.0.0",
        "manifest": "package.json",
        "severity": "HIGH",
    }

    second = {
        **first,
        "manifest": "other-package.json",
    }

    result = deduplicate_findings(
        [first, second]
    )

    assert len(result) == 2


def test_build_summary():
    findings = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"severity": "LOW"},
        {"severity": "UNKNOWN"},
    ]

    result = build_summary(findings)

    assert result == {
        "total": 6,
        "critical": 1,
        "high": 2,
        "medium": 1,
        "low": 1,
        "unknown": 1,
    }