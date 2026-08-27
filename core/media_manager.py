from pathlib import Path

from core.duplicate_checker import calculate_hash, find_duplicate
from core.media_database import DB_FILE, add_media, load_database
from core.media_logger import get_media_logger
from core.media_scanner import (
    PHOTO_DIR,
    SUPPORTED_PHOTOS,
    SUPPORTED_VIDEOS,
    VIDEO_DIR,
)
from core.quality_checker import score_image
from core.queue_manager import queue_metadata


def process_media(
    file_path: Path,
    media_type: str,
    db_file=DB_FILE,
    logger=None,
) -> dict:

    file_path = Path(file_path).resolve()
    logger = logger or get_media_logger()

    database = load_database(db_file)

    # Skip file if it already exists in database.
    existing_name = next(
        (
            item
            for item in database
            if item.get("file") == file_path.name
        ),
        None,
    )

    if existing_name:
        logger.info(
            "SKIPPED_EXISTING | %s",
            file_path.name,
        )
        return existing_name

    # Check duplicate content.
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

    # Process photo.
    elif media_type == "photo":
        quality = score_image(file_path)

        score = quality["score"]

        if score >= 60:
            status = "ready"
        else:
            status = "rejected"

        metadata = {
            "content_hash": content_hash,
            "quality": score,
            "quality_details": quality,
            **queue_metadata(media_type, status),
        }

    # Process video.
    else:
        status = "pending_video_edit"

        metadata = {
            "content_hash": content_hash,
            "quality": None,
            "video_action": (
                "trim_to_approximately_10_seconds_in_next_module"
            ),
            **queue_metadata(media_type, status),
        }

    # Save result to media database.
    add_media(
        file_path.name,
        media_type,
        str(file_path),
        db_file=db_file,
        status=status,
        **metadata,
    )

    record = next(
        item
        for item in load_database(db_file)
        if item.get("file") == file_path.name
    )

    logger.info(
        "PROCESSED | %s | type=%s | status=%s | queue=%s",
        file_path.name,
        media_type,
        status,
        record.get("queue"),
    )

    return record


def process_existing_media(
    db_file=DB_FILE,
    photo_dir=PHOTO_DIR,
    video_dir=VIDEO_DIR,
    logger=None,
) -> list[dict]:

    results = []

    media_sources = (
        (Path(photo_dir), SUPPORTED_PHOTOS, "photo"),
        (Path(video_dir), SUPPORTED_VIDEOS, "video"),
    )

    for folder, extensions, media_type in media_sources:

        if not folder.exists():
            continue

        for file_path in sorted(folder.iterdir()):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in extensions:
                continue

            result = process_media(
                file_path=file_path,
                media_type=media_type,
                db_file=db_file,
                logger=logger,
            )

            results.append(result)

    return results


if __name__ == "__main__":
    processed = process_existing_media()

    print("=" * 55)
    print("MEDIA MANAGER")
    print("=" * 55)

    if not processed:
        print("No media found.")
    else:
        for item in processed:
            print(item)