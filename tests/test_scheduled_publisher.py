import json
from datetime import datetime
from unittest.mock import Mock

from core.media_database import load_database
from core.scheduled_publisher import get_due_posts, publish_due_posts


def _scheduled_database(tmp_path, scheduled_at="2026-08-04T11:30"):
    image = tmp_path / "nails.png"
    image.write_bytes(b"real image")
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps(
            [
                {
                    "file": "nails.png",
                    "path": str(image),
                    "status": "scheduled",
                    "queue": "publish_at_scheduled_time",
                    "scheduled_at": scheduled_at,
                    "caption": "Luxury at your fingertips.",
                    "hashtags": "#One #Two #Three #Four #Five",
                    "posted": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    return db_file


def test_future_post_is_not_due_and_does_not_create_publisher(tmp_path):
    db_file = _scheduled_database(tmp_path)
    factory = Mock()
    results = publish_due_posts(
        db_file=db_file,
        now=datetime(2026, 8, 4, 11, 29),
        posts_dir=tmp_path / "posts",
        publisher_factory=factory,
    )
    assert results == []
    factory.assert_not_called()


def test_due_post_publishes_once_and_saves_ids(tmp_path):
    db_file = _scheduled_database(tmp_path)
    publisher = Mock()
    publisher.publish.return_value = {
        "facebook_post_id": "fb-123",
        "instagram_post_id": "ig-123",
    }
    factory = Mock(return_value=publisher)

    results = publish_due_posts(
        db_file=db_file,
        now=datetime(2026, 8, 4, 11, 30),
        posts_dir=tmp_path / "posts",
        publisher_factory=factory,
    )
    saved = load_database(db_file)[0]

    assert results == [{"file": "nails.png", "status": "published"}]
    assert saved["status"] == "published"
    assert saved["posted"] is True
    assert saved["facebook_post_id"] == "fb-123"
    assert saved["instagram_post_id"] == "ig-123"
    assert get_due_posts(db_file, datetime(2026, 8, 4, 12, 0)) == []
    assert publisher.publish.call_count == 1


def test_failed_publish_moves_to_retry_without_saving_secret_text(tmp_path):
    db_file = _scheduled_database(tmp_path)
    publisher = Mock()
    publisher.publish.side_effect = RuntimeError("token=do-not-save-this")

    results = publish_due_posts(
        db_file=db_file,
        now=datetime(2026, 8, 4, 11, 30),
        posts_dir=tmp_path / "posts",
        publisher_factory=Mock(return_value=publisher),
    )
    saved = load_database(db_file)[0]

    assert results == [{"file": "nails.png", "status": "publish_failed"}]
    assert saved["status"] == "publish_failed"
    assert saved["queue"] == "publish_retry"
    assert saved["publish_error_type"] == "RuntimeError"
    assert "do-not-save-this" not in json.dumps(saved)


def test_due_reel_uses_reel_publisher_and_processed_video(tmp_path):
    reel = tmp_path / "reel.mp4"
    reel.write_bytes(b"reel")
    db_file = tmp_path / "media.json"
    db_file.write_text(json.dumps([{
        "file": "source.mov",
        "type": "video",
        "path": str(tmp_path / "source.mov"),
        "reel_path": str(reel),
        "status": "scheduled",
        "queue": "publish_at_scheduled_time",
        "scheduled_at": "2026-08-04T19:30",
        "caption": "Luxury in motion.",
        "hashtags": "#One #Two #Three #Four #Five",
        "posted": False,
    }]), encoding="utf-8")
    reel_publisher = Mock()
    reel_publisher.publish.return_value = {"facebook_post_id": "fb-r", "instagram_post_id": "ig-r"}
    photo_factory = Mock()

    results = publish_due_posts(
        db_file=db_file,
        now=datetime(2026, 8, 4, 19, 30),
        posts_dir=tmp_path / "posts",
        publisher_factory=photo_factory,
        reel_publisher_factory=Mock(return_value=reel_publisher),
    )

    assert results == [{"file": "source.mov", "status": "published"}]
    photo_factory.assert_not_called()
    package_path = reel_publisher.publish.call_args.args[0]
    package = json.loads(open(package_path, encoding="utf-8").read())
    assert package["video_path"] == str(reel)
    assert package["media_type"] == "reel"
