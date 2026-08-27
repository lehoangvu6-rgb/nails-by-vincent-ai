import json
from datetime import datetime

from core.media_database import load_database
from core.schedule_manager import schedule_approved_posts


def test_schedules_approved_posts_in_separate_prime_slots(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps(
            [
                {"file": "one.jpg", "status": "approved", "queue": "scheduling", "posted": False},
                {"file": "two.jpg", "status": "approved", "queue": "scheduling", "posted": False},
                {"file": "draft.jpg", "status": "draft_ready", "queue": "review", "posted": False},
            ]
        ),
        encoding="utf-8",
    )
    now = datetime(2026, 8, 2, 12, 0)

    results = schedule_approved_posts(db_file, now=now)
    saved = load_database(db_file)

    assert results == [
        {"file": "one.jpg", "scheduled_at": "2026-08-04T11:30"},
        {"file": "two.jpg", "scheduled_at": "2026-08-06T12:30"},
    ]
    assert saved[0]["status"] == "scheduled"
    assert saved[0]["queue"] == "publish_at_scheduled_time"
    assert saved[0]["posted"] is False
    assert saved[2]["status"] == "draft_ready"


def test_scheduling_is_idempotent(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps([{"file": "one.jpg", "status": "approved", "queue": "scheduling"}]),
        encoding="utf-8",
    )
    now = datetime(2026, 8, 2, 12, 0)
    assert len(schedule_approved_posts(db_file, now=now)) == 1
    assert schedule_approved_posts(db_file, now=now) == []


def test_reel_is_scheduled_in_evening_on_a_photo_day(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps([
            {"file": "photo.jpg", "type": "photo", "status": "scheduled", "queue": "publish_at_scheduled_time", "scheduled_at": "2026-08-04T11:30"},
            {"file": "reel.mov", "type": "video", "status": "approved", "queue": "scheduling"},
        ]),
        encoding="utf-8",
    )
    results = schedule_approved_posts(db_file, now=datetime(2026, 8, 3, 10, 0))
    assert results == [{"file": "reel.mov", "scheduled_at": "2026-08-04T19:30"}]


def test_new_reel_is_scheduled_for_the_same_day(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps([
            {
                "file": "today.mov",
                "type": "video",
                "status": "approved",
                "queue": "scheduling",
                "reel_path": "videos/processed/today_reel_10s.mp4",
                "video_edit": {
                    "source_audio_muted": True,
                    "music_status": "licensed_music_added",
                },
            },
        ]),
        encoding="utf-8",
    )

    results = schedule_approved_posts(db_file, now=datetime(2026, 8, 7, 10, 0))
    saved = load_database(db_file)[0]

    assert results == [{"file": "today.mov", "scheduled_at": "2026-08-07T19:30"}]
    assert saved["status"] == "scheduled"
    assert saved["queue"] == "publish_at_scheduled_time"
