"""Découpe un texte en segments (scènes) et extrait des mots-clés
de recherche pour chacun, sans dépendance NLP lourde.
"""
import re

STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et",
    "ou", "mais", "donc", "or", "ni", "car", "que", "qui", "quoi", "dont",
    "où", "ce", "cet", "cette", "ces", "il", "elle", "ils", "elles", "on",
    "nous", "vous", "je", "tu", "se", "sa", "son", "ses", "leur", "leurs",
    "mon", "ma", "mes", "ton", "ta", "tes", "notre", "votre", "à", "en",
    "dans", "sur", "sous", "par", "pour", "avec", "sans", "entre", "vers",
    "chez", "être", "avoir", "est", "sont", "était", "étaient", "a", "ont",
    "fait", "faire", "plus", "moins", "très", "bien", "comme", "aussi",
    "alors", "puis", "ensuite", "quand", "lorsque", "si", "ne", "pas",
    "plus", "d", "l", "qu", "s", "n", "c", "j", "y", "there", "the",
}

WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{3,}")


def split_into_scenes(text: str, max_words_per_scene: int = 25) -> list[str]:
    """Découpe le texte en phrases, puis regroupe en scènes
    d'environ `max_words_per_scene` mots pour garder un rythme cohérent."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    scenes, current, current_len = [], [], 0
    for sentence in sentences:
        words = len(sentence.split())
        if current and current_len + words > max_words_per_scene:
            scenes.append(" ".join(current))
            current, current_len = [], 0
        current.append(sentence)
        current_len += words
    if current:
        scenes.append(" ".join(current))
    return scenes


def extract_keywords(scene_text: str, top_n: int = 3) -> str:
    """Extrait les mots les plus significatifs d'une scène pour
    en faire une requête de recherche d'images/vidéos."""
    words = [w.lower() for w in WORD_RE.findall(scene_text)]
    significant = [w for w in words if w not in STOPWORDS_FR]

    if not significant:
        significant = words

    # fréquence + on garde l'ordre d'apparition pour la pertinence narrative
    seen = {}
    for w in significant:
        seen[w] = seen.get(w, 0) + 1
    ranked = sorted(seen.items(), key=lambda kv: (-kv[1], significant.index(kv[0])))
    keywords = [w for w, _ in ranked[:top_n]]
    return " ".join(keywords) if keywords else "nature"
