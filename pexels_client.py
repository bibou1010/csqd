"""Client léger pour l'API Pexels (photos + vidéos gratuites).
Doc : https://www.pexels.com/api/documentation/
"""
import os
import hashlib
import requests

from config import PEXELS_API_KEY, CACHE_DIR

HEADERS = {"Authorization": PEXELS_API_KEY}
PHOTO_SEARCH_URL = "https://api.pexels.com/v1/search"
VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"


def _cache_path(url: str, ext: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.sha1(url.encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{h}.{ext}")


def _download(url: str, ext: str) -> str:
    path = _cache_path(url, ext)
    if os.path.exists(path):
        return path
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return path


def search_video(query: str, min_width: int = 720):
    """Cherche une vidéo libre de droit correspondant à la requête.
    Retourne le chemin local du fichier téléchargé, ou None."""
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    resp = requests.get(VIDEO_SEARCH_URL, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("videos", [])
    if not results:
        return None

    video = results[0]
    # on choisit le fichier HD le plus proche de la largeur voulue
    files = sorted(video["video_files"], key=lambda f: abs((f.get("width") or 0) - min_width))
    best = files[0]
    return _download(best["link"], "mp4")


def search_photo(query: str):
    """Cherche une photo libre de droit correspondant à la requête.
    Retourne le chemin local du fichier téléchargé, ou None."""
    params = {"query": query, "per_page": 5, "orientation": "portrait"}
    resp = requests.get(PHOTO_SEARCH_URL, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("photos", [])
    if not results:
        return None

    photo = results[0]
    url = photo["src"]["large2x"]
    return _download(url, "jpg")


def fetch_asset_for_scene(query: str):
    """Essaie d'abord une vidéo, puis une photo en repli.
    Retourne (chemin_fichier, type) avec type in {"video", "photo", None}."""
    try:
        video_path = search_video(query)
        if video_path:
            return video_path, "video"
    except requests.RequestException:
        pass

    try:
        photo_path = search_photo(query)
        if photo_path:
            return photo_path, "photo"
    except requests.RequestException:
        pass

    return None, None
