"""Combine plusieurs sources d'images/vidéos libres de droit.
Pour ajouter une nouvelle source : crée un fichier `xxx_client.py` avec les
mêmes fonctions (search_video_candidates, search_photo_candidates, download),
puis ajoute-le dans _active_sources() ci-dessous.
"""
import pexels_client
import pixabay_client
import settings_store


def _active_sources():
    s = settings_store.get()
    sources = []
    if s.get("pexels_api_key"):
        sources.append(pexels_client)
    if s.get("pixabay_api_key"):
        sources.append(pixabay_client)
    return sources


def search_candidates(query: str, count: int = 4, page: int = 1):
    """Cherche des candidats (vidéos puis photos) auprès de toutes les
    sources configurées, et les mélange. `count` = nombre par source/type."""
    candidates = []
    for source in _active_sources():
        try:
            candidates += source.search_video_candidates(query, per_page=count, page=page)
        except Exception:
            pass
        try:
            candidates += source.search_photo_candidates(query, per_page=count, page=page)
        except Exception:
            pass
    return candidates


def download_candidate(candidate: dict) -> str:
    """Télécharge le fichier correspondant au candidat choisi et retourne son chemin local."""
    ext = "mp4" if candidate["type"] == "video" else "jpg"
    client = pexels_client if candidate["source"] == "pexels" else pixabay_client
    return client.download(candidate["download_url"], ext)
