import pytest

from backend.app.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr('backend.app.main.load_local_settings', lambda: None)
    """The API tests use Flask's client; DB integration runs separately."""
    class FakeDB:
        shares = {}
        def init(self):
            pass

        def catalog(self):
            from backend.app.recommender import CATALOG
            return CATALOG

        def photo(self, _):
            return None

        def save_photo(self, *_):
            pass

        def create_share(self, token, key, items):
            self.shares[token] = {"key": key, "items": items}

        def share(self, token):
            return self.shares.get(token)

        def revoke_share(self, token, key):
            if self.shares.get(token, {}).get("key") != key:
                return False
            del self.shares[token]
            return True

    app = create_app(FakeDB())
    app.config.update(TESTING=True)
    return app.test_client()


def test_catalog_route(client):
    response = client.get("/api/catalog")
    assert response.status_code == 200
    assert response.json["cars"]


def test_share_privacy_and_revocation(client):
    car_id = client.get('/api/catalog').json['cars'][0]['id']
    item = {'carId': car_id, 'status': 'мечта'}
    response = client.post('/api/share', json={'items': [{**item, 'note': 'private'}]})
    assert response.status_code == 201
    url = '/api/share/' + response.json['token']
    assert client.get(url).json == {'items': [item]}
    assert client.delete(url).status_code == 404
    assert client.delete(url, headers={'X-Revoke-Key': response.json['revokeKey']}).status_code == 204
    assert client.get(url).status_code == 404


def test_rejects_long_text_and_invalid_budget(client):
    assert client.post("/api/ai/parse-profile", json={"text": "я" * 2001}).status_code == 422
    budget = {"min": 2_000_000, "max": 1_000_000, "status": "provided"}
    assert client.post("/api/recommendation", json={"profile": {"budget": budget}}).status_code == 422


def test_demo_has_filled_garage(client):
    response = client.post("/api/auth/demo", json={"demoKey": "first-car"})
    assert response.status_code == 200
    assert response.json["isDemo"]
    assert len(response.json["garage"]) == 3
