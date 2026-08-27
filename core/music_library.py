import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MUSIC_LIBRARY_DIR = PROJECT_ROOT / "audio" / "library"
MUSIC_MANIFEST = MUSIC_LIBRARY_DIR / "manifest.json"
PREFERRED_GENRES = ("r&b", "r&b and soul", "hip hop", "hip-hop")


def load_music_library(manifest_file=MUSIC_MANIFEST) -> list[dict]:
    manifest_file = Path(manifest_file)
    if not manifest_file.is_file():
        return []
    try:
        tracks = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return tracks if isinstance(tracks, list) else []


def select_vocal_music_track(manifest_file=MUSIC_MANIFEST, *, require_clean_review=True) -> dict:
    tracks = []
    for track in load_music_library(manifest_file):
        path = Path(track.get("path", ""))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        genre = str(track.get("genre", "")).lower()
        if not path.is_file() or not track.get("commercial_use_allowed"):
            continue
        if not track.get("has_vocals") or not any(name in genre for name in PREFERRED_GENRES):
            continue
        if require_clean_review and not track.get("clean_reviewed"):
            continue
        tracks.append({**track, "path": str(path.resolve())})
    if not tracks:
        raise ValueError("No clean, commercial-use R&B/Hip-hop vocal track is ready in the music library.")
    tracks.sort(key=lambda track: (track.get("priority", 999), track.get("times_used", 0)))
    return tracks[0]
