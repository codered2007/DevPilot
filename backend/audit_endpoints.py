
from pathlib import Path

API_DIR = Path(__file__).parent / "app" / "api"

ROUTE_FILES = [
    "repositories.py",
    "chat.py",
    "summary.py",
    "explanation.py",
    "index.py",
    "code_actions.py",
    "apply_code.py",
    "pull_request.py",
    "repository_review.py",
    "architecture_analysis.py",
    "dependency_analysis.py",
    "security_analysis.py",
]

for filename in ROUTE_FILES:
    path = API_DIR / filename

    print(f"\n=== {filename} ===")

    if not path.exists():
        print("FILE MISSING")
        continue

    source = path.read_text(encoding="utf-8")

    print("Uses session dependency:", "get_current_session" in source)
    print("Uses shared repository guard:", "get_accessible_repository" in source)
    print("Uses repository lookup:", "get_repository(" in source)
    print("References access token:", "access_token" in source)