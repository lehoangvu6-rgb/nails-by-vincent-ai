from core.duplicate_checker import calculate_hash, find_duplicate
from core.queue_manager import queue_for


def test_duplicate_is_found_even_with_a_different_name(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "renamed.jpg"
    first.write_bytes(b"same-content")
    second.write_bytes(b"same-content")
    content_hash = calculate_hash(first)
    assert content_hash == calculate_hash(second)
    assert find_duplicate(content_hash, [{"file": "first.jpg", "content_hash": content_hash}])


def test_queue_rules():
    assert queue_for("photo", "ready") == "content_generation"
    assert queue_for("video", "pending_video_edit") == "video_edit_10s"
    assert queue_for("photo", "duplicate") is None
    assert queue_for("photo", "rejected") is None
