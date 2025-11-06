def test_register_and_login_flow(client):
    email = "newuser@example.com"
    password = "secret12345"

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "github_username": "octocat",
        },
    )
    assert r.status_code in (200, 400)
    if r.status_code == 200:
        token = r.json()["access_token"]
        assert token

    lr = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert lr.status_code == 200
    data = lr.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


def test_unauthorized_access_requires_token(client):
    r = client.get("/api/v1/projects/1/analyses")
    assert r.status_code in (401, 403)


