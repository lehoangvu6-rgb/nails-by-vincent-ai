from pathlib import Path

from core.duplicate_checker import calculate_hash, find_duplicate
from core.media_database import DB_FILE, add_media, load_database
from core.media_logger import get_media_logger
from core.media_scanner import PHOTO_DIR, SUPPORTED_PHOTOS, SUPPORTED_VIDEOS, VIDEO_DIR
from core.quality_checker import score_image
from core.queue_manager import queue_metadata


def process_media(file_path: Path, media_type: str, db_file=DB_FILE, logger=None) -> dict:
    file_path = Path(file_path).resolve()
    logger = logger or get_media_logger()
    database = load_database(db_file)
    existing_name = next((item for item in database if item.get("file") == file_path.name), None)
    if existing_name:
        logger.info("SKIPPED_EXISTING | %s", file_path.name)
        return existing_name

    content_hash = calculate_hash(file_path)
    duplicate = find_duplicate(content_hash, database)
    if duplicate:
        status = "duplicate"
        metadata = {
            "content_hash": content_hash,
            "duplicate_of": duplicate["file"],
            "quality": None,
            **queue_metadata(media_type, status),
        }
    elif media_type == "photo":
        quality = score_image(file_path)
        status = quality["status"]
        metadata = {
            "content_hash": content_hash,
            "quality": quality["score"],
            "quality_details": quality,
            **queue_metadata(media_type, status),
        }
    else:
        status = "pending_video_edit"
        metadata = {
            "content_hash": content_hash,
            "quality": None,
            "video_action": "trim_to_approximately_10_seconds_in_next_module",
            **queue_metadata(media_type, status),
        }

    add_media(file_path.name, media_type, str(file_path), db_file=db_file, status=status, **metadata)
    record = next(item for item in load_database(db_file) if item.get("file") == file_path.name)
    logger.info("PROCESSED | %s | type=%s | status=%s | queue=%s", file_path.name, media_type, status, record.get("queue"))
    return record


def process_existing_media(db_file=DB_FILE, photo_dir=PHOTO_DIR, video_dir=VIDEO_DIR, logger=None) -> list[dict]:
    results = []
    for folder, extensions, media_type in (
        (Path(photo_dir), SUPPORTED_PHOTOS, "photo"),
        (Path(video_dir), SUPPORTED_VIDEOS, "video"),
    ):
        if not folder.exists():
            continue
        for file_path in sorted(folder.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                results.append(process_media(file_path, media_type, db_file=db_file, logger=logger))
    return results


if __name__ == "__main__":
    records = process_existing_media()
    print(f"Media Manager processed {len(records)} real media file(s).")
