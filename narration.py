"""Voix off optionnelle via gTTS (Google Text-to-Speech, gratuit)."""
import os
import hashlib
from gtts import gTTS

from config import CACHE_DIR, TTS_LANG


def generate_narration(text: str) -> str:
    """Génère un mp3 de voix off pour le texte donné et renvoie son chemin."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.sha1((text + TTS_LANG).encode()).hexdigest()[:16]
    path = os.path.join(CACHE_DIR, f"tts_{h}.mp3")
    if not os.path.exists(path):
        gTTS(text=text, lang=TTS_LANG).save(path)
    return path
