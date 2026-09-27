"""
Génère une vidéo à partir d'un texte : découpe le récit en scènes,
cherche des images/vidéos libres de droit (Pexels, Pixabay) pour chacune,
et assemble le tout (+ musique de fond + voix off optionnelle).

Usage CLI (choix automatique du 1er résultat pour chaque scène) :
    python main.py --text "Il était une fois..." --output ma_video.mp4
    python main.py --file mon_recit.txt

Pour choisir/changer les images-vidéos scène par scène, utilise l'interface
web (app.py) qui appelle build_scenes() puis assemble_from_selection().
"""
import argparse
import os
import sys

from config import OUTPUT_DIR
from keyword_extractor import split_into_scenes, extract_keywords
import sources
import settings_store
from video_builder import build_scene_clip, assemble_video


def estimate_duration(scene_text: str) -> float:
    """~2.3 mots/seconde en lecture naturelle, avec un minimum."""
    words = len(scene_text.split())
    default_duration = settings_store.get()["default_segment_duration"]
    return max(default_duration, words / 2.3)


def build_scenes(text: str, candidates_per_scene: int = 4):
    """Découpe le texte et cherche les candidats (images/vidéos) pour chaque
    scène, SANS rien télécharger ni assembler. Utilisé par l'interface web
    pour laisser l'utilisateur choisir/changer chaque scène avant génération."""
    scenes = split_into_scenes(text)
    result = []
    for i, scene_text in enumerate(scenes):
        query = extract_keywords(scene_text)
        candidates = sources.search_candidates(query, count=candidates_per_scene, page=1)
        result.append({
            "index": i,
            "text": scene_text,
            "query": query,
            "duration": round(estimate_duration(scene_text), 1),
            "candidates": candidates,
        })
    return result


def more_candidates(query: str, page: int, count: int = 4):
    """Récupère une page supplémentaire de candidats pour une scène
    (bouton "en demander plus" côté interface)."""
    return sources.search_candidates(query, count=count, page=page)


def assemble_from_selection(scenes: list, output_name: str, enable_tts: bool = None, log=print):
    """Assemble la vidéo à partir de scènes dont le candidat (image/vidéo)
    a déjà été choisi. `scenes` = [{"text":..., "candidate": {...}}, ...]"""
    use_tts = settings_store.get()["enable_tts"] if enable_tts is None else enable_tts
    if use_tts:
        from narration import generate_narration

    scene_clips = []
    narration_paths = []

    for i, scene in enumerate(scenes, start=1):
        scene_text = scene["text"]
        candidate = scene.get("candidate")
        if not candidate:
            log(f"   ⚠️  Scène {i} sans candidat sélectionné, ignorée.")
            continue

        log(f"[Scène {i}/{len(scenes)}] téléchargement ({candidate['source']}, {candidate['type']})...")
        asset_path = sources.download_candidate(candidate)

        narration_path = None
        if use_tts:
            narration_path = generate_narration(scene_text)
            from moviepy.editor import AudioFileClip
            duration = AudioFileClip(narration_path).duration
        else:
            duration = estimate_duration(scene_text)

        clip = build_scene_clip(asset_path, candidate["type"], duration)
        scene_clips.append(clip)
        narration_paths.append(narration_path)
        log(f"   ✅ ajouté ({duration:.1f}s)")

    if not scene_clips:
        log("❌ Aucune scène n'a pu être générée.")
        return None

    output_path = os.path.join(OUTPUT_DIR, output_name)
    log("🎬 Assemblage de la vidéo finale...")
    assemble_video(scene_clips, narration_paths, output_path)
    log(f"✅ Vidéo générée : {output_path}")
    return output_path


def run(text: str, output_name: str, enable_tts: bool = None, log=print):
    """Mode automatique (CLI) : prend le 1er candidat trouvé pour chaque scène."""
    scenes = build_scenes(text, candidates_per_scene=1)
    if not scenes:
        log("Texte vide, rien à générer.")
        return None

    log(f"📝 {len(scenes)} scène(s) détectée(s).")

    prepared = []
    for i, scene in enumerate(scenes, start=1):
        log(f"[Scène {i}/{len(scenes)}] mots-clés : \"{scene['query']}\"")
        if not scene["candidates"]:
            log(f"   ⚠️  Aucun résultat pour \"{scene['query']}\", scène ignorée.")
            continue
        prepared.append({"text": scene["text"], "candidate": scene["candidates"][0]})

    return assemble_from_selection(prepared, output_name, enable_tts=enable_tts, log=log)


def main():
    parser = argparse.ArgumentParser(description="Génère une vidéo à partir d'un texte.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Texte directement en argument")
    group.add_argument("--file", type=str, help="Chemin vers un fichier .txt contenant le récit")
    parser.add_argument("--output", type=str, default="video.mp4", help="Nom du fichier de sortie")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Fichier introuvable : {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    run(text, args.output)


if __name__ == "__main__":
    main()
