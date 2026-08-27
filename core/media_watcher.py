import time
import shutil
from pathlib import Path

from core.quality_checker import score_image
from core.media_database import add_media, update_media


MEDIA_DIR = Path("media")
PHOTO_DIR = MEDIA_DIR / "photos"
VIDEO_DIR = MEDIA_DIR / "videos"

READY_DIR = MEDIA_DIR / "ready"
REJECTED_DIR = MEDIA_DIR / "rejected"

SUPPORTED_PHOTOS = {
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"
}

SUPPORTED_VIDEOS = {
    ".mp4", ".mov", ".avi", ".mkv"
}

QUALITY_THRESHOLD = 60


def create_folders():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    READY_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)


def get_files(folder, extensions):
    if not folder.exists():
        return set()

    return {
        file
        for file in folder.iterdir()
        if file.is_file() and file.suffix.lower() in extensions
    }


def process_photo(photo):
    print(f"\nNew photo detected: {photo.name}")

    result = score_image(photo)

    if not result:
        print("Could not analyze photo.")
        return

    quality = result["score"]

    add_media(
        photo.name,
        "photo",
        str(photo)
    )

    print(f"Quality Score: {quality}/100")

    if quality >= QUALITY_THRESHOLD:
        status = "ready"
        destination = READY_DIR / photo.name
        print("Status: READY")
    else:
        status = "rejected"
        destination = REJECTED_DIR / photo.name
        print("Status: REJECTED")

    update_media(
        photo.name,
        quality=quality,
        status=status
    )

    # Keep original photo and make a working copy.
    if not destination.exists():
        shutil.copy2(photo, destination)

    print(f"Database updated: {photo.name}")
    print(f"Working copy: {destination}")


def process_video(video):
    print(f"\nNew video detected: {video.name}")

    add_media(
        video.name,
        "video",
        str(video)
    )

    update_media(
        video.name,
        status="processing"
    )

    print("Status: PROCESSING")
    print("Video queued for ~10-second editing.")


def watch_media(interval_seconds=3):
    create_folders()

    known_photos = get_files(PHOTO_DIR, SUPPORTED_PHOTOS)
    known_videos = get_files(VIDEO_DIR, SUPPORTED_VIDEOS)

    print("=" * 55)
    print("MEDIA WATCHER IS RUNNING")
    print("=" * 55)
    print("Watching media/photos and media/videos")
    print("HEIC / HEIF support: ON")
    print("Press Ctrl + C to stop.")

    try:
        while True:
            current_photos = get_files(
                PHOTO_DIR,
                SUPPORTED_PHOTOS
            )

            current_videos = get_files(
                VIDEO_DIR,
                SUPPORTED_VIDEOS
            )

            new_photos = current_photos - known_photos
            new_videos = current_videos - known_videos

            for photo in sorted(
                new_photos,
                key=lambda x: x.name
            ):
                process_photo(photo)

            for video in sorted(
                new_videos,
                key=lambda x: x.name
            ):
                process_video(video)

            known_photos = current_photos
            known_videos = current_videos

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\nMedia Watcher stopped safely.")


if __name__ == "__main__":
    watch_media()