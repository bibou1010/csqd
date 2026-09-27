"""Client léger pour l'API Pixabay (photos + vidéos gratuites).
Doc : https://pixabay.com/api/docs/
"""
import os
import hashlib
import requests

from config import CACHE_DIR
import settings_store

PHOTO_SEARCH_URL = "https://pixabay.com/api/"
VIDEO_SEARCH_URL = "https://pixabay.com/api/videos/"


def _api_key():
    return settings_store.get()["pixabay_api_key"]


def _cache_path(url: str, ext: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{h}.{ext}")


def download(url: str, ext: str) -> str:
    path = _cache_path(url, ext)
    if os.path.exists(path):
        return path
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return path


def search_video_candidates(query: str, per_page: int = 4, page: int = 1):
    api_key = _api_key()
    if not api_key:
        return []
    per_page = max(per_page, 3)
    params = {"key": api_key, "q": query, "per_page": per_page, "page": page}
    resp = requests.get(VIDEO_SEARCH_URL, params=params, timeout=20)
    resp.raise_for_status()
    candidates = []
    for hit in resp.json().get("hits", []):
        medium = hit.get("videos", {}).get("medium", {})
        if not medium.get("url"):
            continue
        candidates.append({
            "id": f"pixabay_video_{hit['id']}",
            "source": "pixabay",
            "type": "video",
            "thumbnail": medium.get("thumbnail", ""),
            "download_url": medium["url"],
        })
    return candidates


def search_photo_candidates(query: str, per_page: int = 4, page: int = 1):
    api_key = _api_key()
    if not api_key:
        return []
    per_page = max(per_page, 3)
    params = {"key": api_key, "q": query, "per_page": per_page, "page": page, "image_type": "photo"}
    resp = requests.get(PHOTO_SEARCH_URL, params=params, timeout=20)
    resp.raise_for_status()
    candidates = []
    for hit in resp.json().get("hits", []):
        candidates.append({
            "id": f"pixabay_photo_{hit['id']}",
            "source": "pixabay",
            "type": "photo",
            "thumbnail": hit.get("webformatURL", ""),
            "download_url": hit.get("largeImageURL") or hit.get("webformatURL"),
        })
    return candidates
