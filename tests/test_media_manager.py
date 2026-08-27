from PIL import Image

from core.media_database import load_database
from core.media_logger import get_media_logger
from core.media_manager import process_existing_media, process_media


def test_pipeline_prioritizes_real_photos_and_marks_videos_for_next_module(tmp_path):
    photos = tmp_path / "photos"
    videos = tmp_path / "videos"
    photos.mkdir()
    videos.mkdir()
    Image.new("RGB", (1200, 1200), "white").save(photos / "nails.png")
    (videos / "clip.mp4").write_bytes(b"real-video-placeholder")
    db_file = tmp_path / "database.json"
    logger = get_media_logger(tmp_path / "media_manager.log")

    records = process_existing_media(db_file=db_file, photo_dir=photos, video_dir=videos, logger=logger)

    assert [record["type"] for record in records] == ["photo", "video"]
    assert records[0]["status"] == "ready"
    assert records[0]["queue"] == "content_generation"
    assert records[1]["status"] == "pending_video_edit"
    assert records[1]["queue"] == "video_edit_10s"
    assert records[1]["video_action"].startswith("trim_to_approximately_10_seconds")


def test_pipeline_detects_same_content_and_is_idempotent(tmp_path):
    db_file = tmp_path / "database.json"
    first = tmp_path / "first.mp4"
    copy = tmp_path / "copy.mp4"
    first.write_bytes(b"same-video")
    copy.write_bytes(b"same-video")
    logger = get_media_logger(tmp_path / "media_manager.log")

    process_media(first, "video", db_file=db_file, logger=logger)
    duplicate = process_media(copy, "video", db_file=db_file, logger=logger)
    process_media(first, "video", db_file=db_file, logger=logger)

    assert duplicate["status"] == "duplicate"
    assert duplicate["duplicate_of"] == "first.mp4"
    assert len(load_database(db_file)) == 2
