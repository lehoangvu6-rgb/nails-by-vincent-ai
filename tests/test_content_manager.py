import json

from core.content_manager import (
    get_content_queue,
    get_reel_content_queue,
    process_content_queue,
    process_reel_content_queue,
)


def _write_database(path, records):
    path.write_text(json.dumps(records), encoding="utf-8")


def test_only_ready_real_photo_enters_content_queue(tmp_path):
    db_file = tmp_path / "media.json"
    _write_database(
        db_file,
        [
            {"file": "ready-photo.jpg", "type": "photo", "status": "ready", "queue": "content_generation"},
            {"file": "bad-photo.jpg", "type": "photo", "status": "rejected", "queue": None},
            {"file": "clip.mp4", "type": "video", "status": "pending_video_edit", "queue": "video_edit_10s"},
        ],
    )

    queued = get_content_queue(db_file)
    assert [item["file"] for item in queued] == ["ready-photo.jpg"]


def test_draft_uses_real_media_and_moves_to_review(tmp_path):
    db_file = tmp_path / "media.json"
    _write_database(
        db_file,
        [{"file": "pink_chrome.jpg", "type": "photo", "status": "ready", "queue": "content_generation"}],
    )

    drafts = process_content_queue(db_file)
    saved = json.loads(db_file.read_text(encoding="utf-8"))[0]

    assert len(drafts) == 1
    assert saved["caption"]
    assert saved["hashtags"].startswith("#NailsByVincent")
    assert len(saved["hashtags"].split()) == 5
    assert saved["cta"]
    assert saved["uses_real_media"] is True
    assert saved["ai_image_generated"] is False
    assert saved["status"] == "draft_ready"
    assert saved["queue"] == "review"


def test_no_ready_photo_creates_no_draft(tmp_path):
    db_file = tmp_path / "media.json"
    _write_database(db_file, [{"file": "bad.jpg", "type": "photo", "status": "rejected", "queue": None}])
    assert process_content_queue(db_file) == []


def test_reel_draft_uses_processed_real_video_and_five_hashtags(tmp_path):
    db_file = tmp_path / "media.json"
    _write_database(
        db_file,
        [{
            "file": "clip.mov",
            "type": "video",
            "status": "reel_ready",
            "queue": "reel_content_generation",
            "reel_path": "videos/processed/clip_reel_10s.mp4",
        }],
    )

    assert len(get_reel_content_queue(db_file)) == 1
    drafts = process_reel_content_queue(db_file)
    saved = json.loads(db_file.read_text(encoding="utf-8"))[0]

    assert len(drafts) == 1
    assert len(saved["hashtags"].split()) == 5
    assert saved["status"] == "reel_draft_ready"
    assert saved["queue"] == "review"
    assert saved["uses_real_media"] is True
    assert saved["ai_image_generated"] is False
