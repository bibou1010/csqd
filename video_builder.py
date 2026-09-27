"""Construit la vidéo finale à partir des scènes (images/vidéos + audio)."""
import os
import glob
import random

from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    concatenate_videoclips,
    concatenate_audioclips,
)

from config import FPS, MUSIC_DIR
import settings_store


def _ken_burns_clip(image_path: str, duration: float):
    """Crée un léger effet de zoom lent (Ken Burns) sur une image fixe."""
    width, height = settings_store.video_dimensions()
    clip = ImageClip(image_path).set_duration(duration)
    clip = clip.resize(height=height)
    if clip.w < width:
        clip = clip.resize(width=width)

    zoom_ratio = 1.12  # zoom final à 112%
    clip = clip.resize(lambda t: 1 + (zoom_ratio - 1) * (t / duration))
    clip = clip.set_position(("center", "center"))
    return CompositeVideoClip([clip], size=(width, height)).set_duration(duration)


def _video_scene_clip(video_path: str, duration: float):
    width, height = settings_store.video_dimensions()
    clip = VideoFileClip(video_path)
    if clip.duration < duration:
        # on boucle si la vidéo source est trop courte
        loops = int(duration // clip.duration) + 1
        clip = concatenate_videoclips([clip] * loops)
    clip = clip.subclip(0, duration)
    clip = clip.resize(height=height)
    if clip.w < width:
        clip = clip.resize(width=width)
    clip = clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=width, height=height)
    return clip.without_audio()


def build_scene_clip(asset_path: str, asset_type: str, duration: float):
    if asset_type == "video":
        return _video_scene_clip(asset_path, duration)
    return _ken_burns_clip(asset_path, duration)


def _pick_background_music(total_duration: float):
    tracks = glob.glob(os.path.join(MUSIC_DIR, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, "*.wav"))
    if not tracks:
        return None
    track_path = random.choice(tracks)
    music = AudioFileClip(track_path)
    if music.duration < total_duration:
        loops = int(total_duration // music.duration) + 1
        music = concatenate_audioclips([music] * loops)
    music = music.subclip(0, total_duration).volumex(settings_store.get()["music_volume"])
    return music


def assemble_video(scene_clips: list, narration_paths: list, output_path: str):
    """Concatène les scènes, ajoute la voix off (si fournie) et la musique de fond."""
    final_video = concatenate_videoclips(scene_clips, method="compose")
    total_duration = final_video.duration

    audio_tracks = []

    narration_clips = [p for p in narration_paths if p]
    if narration_clips:
        narration_audio = concatenate_audioclips([AudioFileClip(p) for p in narration_clips])
        audio_tracks.append(narration_audio)

    music = _pick_background_music(total_duration)
    if music:
        audio_tracks.append(music)

    if audio_tracks:
        final_video = final_video.set_audio(CompositeAudioClip(audio_tracks))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )
    return output_path
