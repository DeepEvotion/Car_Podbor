import json
import re
from html import unescape
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
from .catalog_extra import ROWS

PHOTO_TITLES = {
    "lada-granta-sedan-ii": "Lada Granta",
    "hyundai-solaris-ii": "Hyundai Solaris",
    "skoda-octavia-iv": "Škoda Octavia",
    "kia-sportage-v": "Kia Sportage",
    "toyota-rav4-v": "Toyota RAV4",
    "renault-duster-ii": "Dacia Duster",
    "lada-niva-travel": "Lada Niva Travel",
    "volkswagen-tiguan-ii": "Volkswagen Tiguan",
    "mazda-cx5-ii": "Mazda CX-5",
    "honda-crv-v": "Honda CR-V",
    "ford-focus-iv-wagon": "Ford Focus wagon",
    "volkswagen-golf-viii": "Volkswagen Golf",
    "mini-cooper-f56": "Mini Cooper",
    "tesla-model-3": "Tesla Model 3",
    "moskvich-3e": "Moskvich 3",
    "geely-tugella-i": "Geely Tugella",
    "kia-carnival-iv": "Kia Carnival",
    "toyota-highlander-iv": "Toyota Highlander",
    "subaru-outback-vi": "Subaru Outback",
    "porsche-718-cayman": "Porsche 718 Cayman",
    "citroen-c4-cactus": "Citroën C4 Cactus",
    "volvo-xc90-ii": "Volvo XC90",
    "nissan-leaf-ii": "Nissan Leaf",
    "suzuki-jimny-iv": "Suzuki Jimny",
}
PHOTO_TITLES.update({row[0]: f"{row[1]} {row[2]}" for row in ROWS})

cache = {}


def _plain_credit(value):
    """Convert provider metadata to safe, readable plain text."""
    if not isinstance(value, str):
        return ""
    value = unescape(value)
    value = re.sub(r"<[^>]*>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:220]


def _allowed(url):
    """Allow image CDN URLs returned by Openverse."""
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError):
        return False
    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in {"images.openverse.org", "live.staticflickr.com", "upload.wikimedia.org"}
        and parsed.path not in {"", "/"}
    )


def find_photo(car_id):
    if car_id in cache:
        return cache[car_id]
    title = PHOTO_TITLES.get(car_id)
    if not title:
        return None
    params = urlencode({"q": title, "page_size": 12, "license_type": "commercial", "mature": "false"})
    request = Request(
        f"https://api.openverse.org/v1/images/?{params}",
        headers={"User-Agent": "CarMatch/1.0 (open image catalogue)"},
    )
    try:
        with urlopen(request, timeout=7) as response:
            pages = json.loads(response.read(524288)).get("results", [])
        results = []
        for page in pages:
            image_url = page.get("thumbnail") or page.get("url")
            if not image_url or not _allowed(image_url):
                continue
            result = {
                "url": image_url,
                "source": page.get("foreign_landing_url") or page.get("detail_url") or "https://openverse.org/",
                "credit": _plain_credit(" · ".join(value for value in (page.get("creator"), page.get("license")) if value)),
            }
            results.append(result)
            if len(results) >= 3:
                break
        if results:
            result = {"url": results[0]["url"], "source": results[0]["source"], "credit": results[0]["credit"], "photos": results}
            if results[0].get("originalUrl"):
                result["originalUrl"] = results[0]["originalUrl"]
            cache[car_id] = result
            return result
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        pass
    # Compatibility fallback for old Commons responses and temporary Openverse outages.
    return _find_commons_photo(car_id, title)


def _find_commons_photo(car_id, title):
    params = urlencode({"action": "query", "generator": "search", "gsrsearch": f"{title} filetype:bitmap", "gsrnamespace": 6,
                        "gsrlimit": 8, "prop": "imageinfo", "iiprop": "url|mime|extmetadata", "iiurlwidth": 960,
                        "format": "json", "formatversion": 2})
    request = Request(f"https://commons.wikimedia.org/w/api.php?{params}", headers={"User-Agent": "CarMatch/1.0"})
    try:
        with urlopen(request, timeout=7) as response:
            pages = json.loads(response.read(262144)).get("query", {}).get("pages", [])
        for page in pages:
            image = (page.get("imageinfo") or [{}])[0]
            urls = [url for url in (image.get("thumburl"), image.get("url")) if url and urlparse(url).netloc.lower() == "upload.wikimedia.org"]
            license_name = ((image.get("extmetadata") or {}).get("LicenseShortName") or {}).get("value")
            artist = ((image.get("extmetadata") or {}).get("Artist") or {}).get("value", "")
            if urls and license_name:
                result = {"url": urls[0], "source": "https://commons.wikimedia.org/wiki/" + quote(page.get("title", ""), safe=""),
                          "credit": _plain_credit(" · ".join(value for value in (artist, license_name) if value))}
                cache[car_id] = result
                return result
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        pass
    return None
