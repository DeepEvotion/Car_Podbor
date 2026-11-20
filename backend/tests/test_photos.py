import json
from io import BytesIO

from backend.app import photos


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        return json.dumps({
            "query": {
                "pages": [{
                    "title": "File:Test car.jpg",
                    "imageinfo": [{
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/test.jpg/1000px-test.jpg",
                        "extmetadata": {
                            "Artist": {"value": "Photographer"},
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                        },
                    }],
                }],
            },
        }).encode()


def test_commons_photo_is_validated_and_cached(monkeypatch):
    photos.cache.clear()
    monkeypatch.setattr(photos, "urlopen", lambda *args, **kwargs: Response())
    result = photos.find_photo("lada-granta-sedan-ii")
    assert result["url"].startswith("https://upload.wikimedia.org/wikipedia/commons/")
    assert result["credit"] == "Photographer · CC BY-SA 4.0"
    assert photos.find_photo("lada-granta-sedan-ii") is result


def test_only_direct_commons_urls_are_allowed():
    assert photos._allowed("https://upload.wikimedia.org/wikipedia/commons/thumb/a/test.jpg/1000px-test.jpg")
    assert photos._allowed("https://upload.wikimedia.org/wikipedia/commons/a/test.jpg")
    assert not photos._allowed("https://commons.wikimedia.org/wiki/File:Test.jpg")
    assert not photos._allowed("https://example.com/wikipedia/commons/a/test.jpg")
