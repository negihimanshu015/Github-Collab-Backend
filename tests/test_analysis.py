from tests.conftest import auth_headers


def test_code_review_analysis_flow(client, auth_token, monkeypatch):
    # Mock AI service
    import src.api.routes as routes

    def mock_generate_code_review(code: str, context: str = ""):
        return "Review: Looks good."

    routes.gemini_service.generate_code_review = mock_generate_code_review

    # Create a project
    pr = client.post(
        "/api/v1/projects",
        headers=auth_headers(auth_token),
        json={
            "name": "Analysis Project",
            "description": "For analysis",
            "github_repo": "https://github.com/owner/repo",
        },
    )
    assert pr.status_code == 200, pr.text
    project_id = pr.json()["id"]

    # Perform code review
    cr = client.post(
        "/api/v1/analyze/code-review",
        headers=auth_headers(auth_token),
        json={
            "project_id": project_id,
            "code": "print('hello')",
            "context": "simple script",
        },
    )
    assert cr.status_code == 200, cr.text
    data = cr.json()
    assert "Review:" in data["review"]
    assert data["analysis_id"]


def test_documentation_and_bug_detection(client, auth_token, monkeypatch):
    import src.api.routes as routes

    routes.gemini_service.generate_documentation = lambda code: "# Docs\nThis does X"
    routes.gemini_service.detect_bugs = lambda code: "No obvious bugs"

    # Create a project
    pr = client.post(
        "/api/v1/projects",
        headers=auth_headers(auth_token),
        json={
            "name": "Docs Project",
            "description": "Docs & Bugs",
            "github_repo": "https://github.com/owner/repo",
        },
    )
    assert pr.status_code == 200

    dr = client.post(
        "/api/v1/analyze/documentation",
        headers=auth_headers(auth_token),
        json={"code": "def add(a,b): return a+b"},
    )
    assert dr.status_code == 200
    assert dr.json()["documentation"].startswith("# Docs")

    br = client.post(
        "/api/v1/analyze/bug-detection",
        headers=auth_headers(auth_token),
        json={"code": "x=1"},
    )
    assert br.status_code == 200
    assert "bugs" in br.json()


