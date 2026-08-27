import json
from pathlib import Path

from core.media_database import load_database
from core.reel_editor import (
    create_daily_ai_reel_if_needed,
    create_reel_from_photos,
    edit_reel,
    get_video_edit_queue,
    process_video_queue,
)


def test_edit_reel_keeps_source_and_uses_center_ten_seconds(monkeypatch, tmp_path):
    source = tmp_path / "original.mov"
    source.write_bytes(b"original video")
    music = tmp_path / "licensed.wav"
    music.write_bytes(b"licensed music")
    output_dir = tmp_path / "processed"
    calls = []

    def fake_probe(path):
        if Path(path) == source.resolve():
            return {"duration": 30.0, "fps": 30.0, "size": (1920, 1080), "codec": "h264"}
        return {"duration": 10.0, "fps": 30.0, "size": (1920, 1080), "codec": "h264"}

    def fake_run(command, **kwargs):
        calls.append(command)
        Path(command[-1]).write_bytes(b"edited reel")

    monkeypatch.setattr("core.reel_editor.probe_video", fake_probe)
    monkeypatch.setattr("core.reel_editor.subprocess.run", fake_run)

    result = edit_reel(source, output_dir=output_dir, music_path=music)

    assert source.read_bytes() == b"original video"
    assert result["clip_start"] == 10.0
    assert result["reel_duration"] == 10.0
    assert Path(result["output_path"]).name == "original_reel_10s.mp4"
    edit_command = calls[-1]
    assert edit_command[edit_command.index("-t") + 1] == "10.000"
    assert "scale=1080:1920" in edit_command[edit_command.index("-vf") + 1]
    assert "-an" not in edit_command
    assert edit_command[edit_command.index("-map") + 1] == "0:v:0"
    assert "1:a:0" in edit_command
    assert result["source_audio_muted"] is True
    assert result["music_status"] == "licensed_music_added"


def test_edit_reel_refuses_to_export_without_music(monkeypatch, tmp_path):
    source = tmp_path / "original.mov"
    source.write_bytes(b"original video")
    monkeypatch.setattr(
        "core.reel_editor.probe_video",
        lambda path: {"duration": 12.0, "fps": 30.0, "size": (1080, 1920), "codec": "h264"},
    )

    try:
        edit_reel(source, output_dir=tmp_path / "processed")
    except ValueError as exc:
        assert "music track is required" in str(exc)
    else:
        raise AssertionError("Reel without replacement music must not be exported")


def test_process_queue_updates_database(monkeypatch, tmp_path):
    source = tmp_path / "clip.mov"
    source.write_bytes(b"video")
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps([{"file": "clip.mov", "path": str(source), "type": "video", "status": "pending_video_edit", "queue": "video_edit_10s"}]),
        encoding="utf-8",
    )
    reel_path = tmp_path / "clip_reel_10s.mp4"
    monkeypatch.setattr(
        "core.reel_editor.edit_reel",
        lambda *args, **kwargs: {
            "source_path": str(source), "output_path": str(reel_path),
            "source_duration": 20.0, "reel_duration": 10.0, "clip_start": 5.0,
            "source_size": (1080, 1920), "output_size": (1080, 1920),
            "source_audio_muted": True,
            "music_status": "original_royalty_free_music_added",
            "music_path": "audio/generated/test.wav",
        },
    )

    results = process_video_queue(db_file, tmp_path / "processed")
    saved = load_database(db_file)[0]

    assert results[0]["status"] == "reel_ready"
    assert saved["status"] == "reel_ready"
    assert saved["queue"] == "reel_content_generation"
    assert saved["reel_path"] == str(reel_path)
    assert get_video_edit_queue(db_file) == []


def test_creates_daily_reel_from_ai_images_when_there_is_no_video(monkeypatch, tmp_path):
    music = tmp_path / "licensed.wav"
    music.write_bytes(b"music")
    db_file = tmp_path / "media.json"
    db_file.write_text(
        "[]",
        encoding="utf-8",
    )
    generated = []

    def fake_generate(prompt):
        path = tmp_path / f"ai_{len(generated)}.png"
        path.write_bytes(b"ai image")
        generated.append(path)
        return str(path)

    output_path = tmp_path / "processed" / "daily_ai_reel_20260807.mp4"
    monkeypatch.setattr(
        "core.music_library.select_vocal_music_track",
        lambda: {
            "path": str(music),
            "title": "Clean Vocal",
            "artist": "Test Artist",
            "source": "Meta Sound Collection",
            "hook_start_seconds": 0,
        },
    )
    monkeypatch.setattr(
        "core.reel_editor.create_reel_from_photos",
        lambda photos, output, **kwargs: {
            "output_path": str(output_path),
            "reel_duration": 10.0,
            "output_size": (1080, 1920),
            "source_photos": [str(path) for path in photos],
            "source_audio_muted": True,
            "music_status": "licensed_music_added",
            "music_path": str(music),
            "creation_method": "real_photo_montage",
            "ai_image_generated": False,
        },
    )

    result = create_daily_ai_reel_if_needed(
        db_file=db_file,
        output_dir=tmp_path / "processed",
        now=__import__("datetime").datetime(2026, 8, 7, 10, 0),
        image_generator=fake_generate,
    )
    saved = load_database(db_file)[-1]

    assert result["status"] == "reel_ready"
    assert saved["queue"] == "reel_content_generation"
    assert len(generated) == 3
    assert saved["generated_from_ai_images"] is True
    assert saved["video_edit"]["source_audio_muted"] is True
    assert saved["ai_image_generated"] is True
