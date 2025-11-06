from tests.conftest import auth_headers


def test_repo_endpoints_with_mocks(client, auth_token, monkeypatch):
    import src.api.routes as routes

    # Mock GitHub service
    routes.github_service.get_user_repos = lambda username: [
        {
            "name": "repo1",
            "full_name": f"{username}/repo1",
            "description": "Test repo",
            "url": "https://api.github.com/repos/user/repo1",
            "language": "Python",
            "stars": 10,
            "forks": 1,
        }
    ]

    # Simple content tree: root has a folder and a file
    def mock_get_repo_content(full_name: str, path: str = ""):
        if path == "":
            return [
                {"name": "src", "path": "src", "type": "dir", "size": 0, "url": ""},
                {"name": "main.py", "path": "main.py", "type": "file", "size": 10, "url": ""},
            ]
        if path == "src":
            return [
                {"name": "app.py", "path": "src/app.py", "type": "file", "size": 10, "url": ""}
            ]
        return []

    routes.github_service.get_repo_content = mock_get_repo_content
    routes.github_service.get_file_content = lambda full_name, path: "print('hi')"

    # Mock LangChain no-ops
    routes.langchain_service.process_code_documents = lambda docs: docs
    routes.langchain_service.create_vector_store = lambda docs: None

    # Mock create issue
    routes.github_service.create_issue = lambda full_name, title, body: {
        "number": 1,
        "title": title,
        "body": body,
        "url": "https://api.github.com/repos/user/repo1/issues/1",
    }

    # Get user repos
    rr = client.get(
        "/api/v1/user/repos",
        headers=auth_headers(auth_token),
        params={"username": "user"},
    )
    assert rr.status_code == 200
    assert len(rr.json()["repos"]) == 1

    # Repo content
    rc = client.get(
        "/api/v1/repo/content",
        headers=auth_headers(auth_token),
        params={"repo_url": "https://github.com/user/repo1", "path": ""},
    )
    assert rc.status_code == 200
    assert isinstance(rc.json()["content"], list)

    # Full repo analysis
    fa = client.post(
        "/api/v1/repo/analyze-complete",
        headers=auth_headers(auth_token),
        json={"repo_url": "https://github.com/user/repo1"},
    )
    assert fa.status_code == 200, fa.text
    data = fa.json()
    assert data["files_analyzed"] >= 1
    assert "overall_analysis" in data

    # Create issue
    ci = client.post(
        "/api/v1/issues/create",
        headers=auth_headers(auth_token),
        json={
            "repo_url": "https://github.com/user/repo1",
            "title": "Bug: something",
            "body": "There is a problem",
        },
    )
    assert ci.status_code == 200
    assert ci.json()["issue"]["number"] == 1


