def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert "version" in data


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    # Backend returns "healthy"; accept either to be robust
    assert data.get("status") in ("ok", "healthy")
    assert "timestamp" in data


