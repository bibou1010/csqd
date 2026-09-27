"""Configuration centrale du projet, chargée depuis .env"""
import os
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").lower() == "true"
TTS_LANG = os.getenv("TTS_LANG", "fr")
MUSIC_DIR = os.getenv("MUSIC_DIR", "assets/music")
MUSIC_VOLUME = float(os.getenv("MUSIC_VOLUME", "0.15"))
DEFAULT_SEGMENT_DURATION = float(os.getenv("DEFAULT_SEGMENT_DURATION", "4.5"))

CACHE_DIR = "assets/cache"
OUTPUT_DIR = "assets/output"
SFX_DIR = "assets/sfx"

# Résolution de la vidéo finale
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # format vertical (réseaux sociaux) ; mets 1920x1080 pour du paysage
FPS = 30

if not PEXELS_API_KEY:
    print(
        "⚠️  Aucune clé PEXELS_API_KEY trouvée. Copie .env.example en .env "
        "et renseigne ta clé (inscription gratuite sur pexels.com/api)."
    )
