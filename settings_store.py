"""Réglages modifiables à chaud depuis l'interface web (page /settings),
stockés dans un fichier JSON local. Les variables d'environnement (.env)
servent de valeurs par défaut au premier lancement.

⚠️ Sur un hébergement avec disque éphémère (ex. Render plan gratuit), ce
fichier peut être réinitialisé après une mise en veille/redémarrage — pour
des réglages qui doivent survivre à un redéploiement, utilise plutôt les
variables d'environnement du panneau Render.
"""
import json
import os
import threading

import config

SETTINGS_FILE = os.path.join("data", "settings.json")
_lock = threading.Lock()

DEFAULTS = {
    "pexels_api_key": config.PEXELS_API_KEY,
    "pixabay_api_key": config.PIXABAY_API_KEY,
    "candidates_per_scene": config.CANDIDATES_PER_SCENE,
    "music_volume": config.MUSIC_VOLUME,
    "enable_tts": config.ENABLE_TTS,
    "tts_lang": config.TTS_LANG,
    "orientation": "portrait" if config.VIDEO_WIDTH < config.VIDEO_HEIGHT else "landscape",
    "default_segment_duration": config.DEFAULT_SEGMENT_DURATION,
}


def get():
    """Retourne les réglages actuels (fichier JSON s'il existe, sinon défauts .env)."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = DEFAULTS.copy()
            merged.update(data)
            return merged
        except Exception:
            pass
    return DEFAULTS.copy()


def save(updates: dict):
    """Fusionne et enregistre les nouveaux réglages."""
    with _lock:
        current = get()
        current.update(updates)
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        return current


def video_dimensions():
    s = get()
    if s["orientation"] == "landscape":
        return 1920, 1080
    return 1080, 1920
