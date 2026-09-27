"""
Génère une vidéo à partir d'un texte : découpe le récit en scènes,
cherche des images/vidéos libres de droit sur Pexels pour chacune,
et assemble le tout (+ musique de fond + voix off optionnelle).

Usage :
    python main.py --text "Il était une fois..." --output ma_video.mp4
    python main.py --file mon_recit.txt
"""
import argparse
import os
import sys

from config import ENABLE_TTS as ENABLE_TTS_DEFAULT, DEFAULT_SEGMENT_DURATION, OUTPUT_DIR
from keyword_extractor import split_into_scenes, extract_keywords
from pexels_client import fetch_asset_for_scene
from video_builder import build_scene_clip, assemble_video


def estimate_duration(scene_text: str) -> float:
    """~2.3 mots/seconde en lecture naturelle, avec un minimum."""
    words = len(scene_text.split())
    return max(DEFAULT_SEGMENT_DURATION, words / 2.3)


def run(text: str, output_name: str, enable_tts: bool = None, log=print):
    """Génère la vidéo. `log` reçoit chaque message de progression
    (utilisé par l'interface web pour afficher l'avancement en direct)."""
    use_tts = ENABLE_TTS_DEFAULT if enable_tts is None else enable_tts
    if use_tts:
        from narration import generate_narration

    scenes = split_into_scenes(text)
    if not scenes:
        log("Texte vide, rien à générer.")
        return None

    log(f"📝 {len(scenes)} scène(s) détectée(s).")

    scene_clips = []
    narration_paths = []

    for i, scene_text in enumerate(scenes, start=1):
        query = extract_keywords(scene_text)
        log(f"[Scène {i}/{len(scenes)}] mots-clés : \"{query}\"")

        asset_path, asset_type = fetch_asset_for_scene(query)
        if not asset_path:
            log(f"   ⚠️  Aucun résultat pour \"{query}\", scène ignorée.")
            continue

        narration_path = None
        if use_tts:
            narration_path = generate_narration(scene_text)
            from moviepy.editor import AudioFileClip
            duration = AudioFileClip(narration_path).duration
        else:
            duration = estimate_duration(scene_text)

        clip = build_scene_clip(asset_path, asset_type, duration)
        scene_clips.append(clip)
        narration_paths.append(narration_path)
        log(f"   ✅ {asset_type} ajouté ({duration:.1f}s)")

    if not scene_clips:
        log("❌ Aucune scène n'a pu être générée (vérifie ta clé API Pexels).")
        return None

    output_path = os.path.join(OUTPUT_DIR, output_name)
    log("🎬 Assemblage de la vidéo finale...")
    assemble_video(scene_clips, narration_paths, output_path)
    log(f"✅ Vidéo générée : {output_path}")
    return output_path


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
