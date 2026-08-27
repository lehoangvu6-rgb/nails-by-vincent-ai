import json

import pytest

from core.music_library import select_vocal_music_track


def test_selects_clean_commercial_vocal_hip_hop_track(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"audio")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{
        "title": "Clean Vocal",
        "path": str(audio),
        "genre": "Hip Hop",
        "has_vocals": True,
        "commercial_use_allowed": True,
        "clean_reviewed": True,
    }]), encoding="utf-8")
    assert select_vocal_music_track(manifest)["title"] == "Clean Vocal"


def test_refuses_unreviewed_vocal_track(tmp_path):
    audio = tmp_path / "track.mp3"
    audio.write_bytes(b"audio")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{
        "title": "Needs Review",
        "path": str(audio),
        "genre": "R&B and Soul",
        "has_vocals": True,
        "commercial_use_allowed": True,
        "clean_reviewed": False,
    }]), encoding="utf-8")
    with pytest.raises(ValueError, match="No clean"):
        select_vocal_music_track(manifest)
