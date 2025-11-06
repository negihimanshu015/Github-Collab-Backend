from tests.conftest import auth_headers


def test_codebase_query(client, auth_token, monkeypatch):
    import src.api.routes as routes

    routes.langchain_service.query_codebase = lambda question: {
        "answer": "This is a mock answer.",
        "sources": [],
    }

    r = client.post(
        "/api/v1/query/codebase",
        headers=auth_headers(auth_token),
        json={"question": "What does the app do?"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data["response"], dict)


