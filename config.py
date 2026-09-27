"""Configuration centrale du projet, chargée depuis .env"""
import os
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")  # optionnel — source supplémentaire, gratuite sur pixabay.com/api/docs
CANDIDATES_PER_SCENE = int(os.getenv("CANDIDATES_PER_SCENE", "4"))
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

if not PEXELS_API_KEY and not PIXABAY_API_KEY:
    print(
        "⚠️  Aucune clé API trouvée (PEXELS_API_KEY / PIXABAY_API_KEY). "
        "Copie .env.example en .env et renseigne au moins une clé."
    )
