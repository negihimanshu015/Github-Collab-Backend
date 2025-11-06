from tests.conftest import auth_headers


def test_create_project_and_list_analyses_initially_empty(client, auth_token):
    # Create a project
    pr = client.post(
        "/api/v1/projects",
        headers=auth_headers(auth_token),
        json={
            "name": "My Project",
            "description": "Test project",
            "github_repo": "https://github.com/owner/repo",
        },
    )
    assert pr.status_code == 200, pr.text
    project = pr.json()
    project_id = project["id"]

    # List analyses for the project (should be empty)
    ar = client.get(
        f"/api/v1/projects/{project_id}/analyses",
        headers=auth_headers(auth_token),
    )
    assert ar.status_code == 200, ar.text
    assert isinstance(ar.json(), list)
    assert len(ar.json()) == 0


