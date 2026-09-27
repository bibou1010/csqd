"""Client léger pour l'API Pexels (photos + vidéos gratuites).
Doc : https://www.pexels.com/api/documentation/
"""
import os
import hashlib
import requests

from config import CACHE_DIR
import settings_store

PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"
VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"


def _api_key():
    return settings_store.get()["pexels_api_key"]


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
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "page": page, "orientation": "portrait"}
    resp = requests.get(VIDEO_SEARCH_URL, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    candidates = []
    for video in resp.json().get("videos", []):
        files = sorted(video.get("video_files", []), key=lambda f: abs((f.get("width") or 0) - 720))
        if not files:
            continue
        pictures = video.get("video_pictures", [])
        thumbnail = pictures[0]["picture"] if pictures else video.get("image", "")
        candidates.append({
            "id": f"pexels_video_{video['id']}",
            "source": "pexels",
            "type": "video",
            "thumbnail": thumbnail,
            "download_url": files[0]["link"],
        })
    return candidates


def search_photo_candidates(query: str, per_page: int = 4, page: int = 1):
    api_key = _api_key()
    if not api_key:
        return []
    headers = {"Authorization": api_key}
    params = {"query": query, "per_page": per_page, "page": page, "orientation": "portrait"}
    resp = requests.get(PHOTO_SEARCH_URL, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    candidates = []
    for photo in resp.json().get("photos", []):
        candidates.append({
            "id": f"pexels_photo_{photo['id']}",
            "source": "pexels",
            "type": "photo",
            "thumbnail": photo["src"]["medium"],
            "download_url": photo["src"]["large2x"],
        })
    return candidates
