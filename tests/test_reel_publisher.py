import json
from unittest.mock import Mock, patch

from publishers.reel_publisher import ReelPublisher


def _environment(monkeypatch):
    monkeypatch.setenv("META_GRAPH_API_VERSION", "v25.0")
    monkeypatch.setenv("META_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "page-1")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "ig-1")


def test_reel_publisher_posts_both_platforms(monkeypatch, tmp_path):
    _environment(monkeypatch)
    video = tmp_path / "reel.mp4"
    video.write_bytes(b"video")
    package = tmp_path / "post.json"
    package.write_text(json.dumps({
        "caption": "Luxury in motion.",
        "hashtags": "#One #Two #Three #Four #Five",
        "video_path": str(video),
    }), encoding="utf-8")
    publisher = ReelPublisher()

    with (
        patch.object(publisher.facebook, "publish_reel", return_value={"id": "fb-reel"}),
        patch.object(publisher, "_video_url", return_value="https://example.com/reel.mp4"),
        patch.object(publisher.instagram, "publish_reel_from_url", return_value={"id": "ig-reel"}),
    ):
        result = publisher.publish(str(package))

    assert result["status"] == "published"
    assert result["facebook_post_id"] == "fb-reel"
    assert result["instagram_post_id"] == "ig-reel"
    saved = json.loads(package.read_text(encoding="utf-8"))
    assert saved["status"] == "published"
