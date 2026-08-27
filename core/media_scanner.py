from pathlib import Path
from datetime import datetime

MEDIA_DIR = Path("media")

PHOTO_DIR = MEDIA_DIR / "photos"
VIDEO_DIR = MEDIA_DIR / "videos"

SUPPORTED_PHOTOS = [".jpg", ".jpeg", ".png", ".webp",".heic",".heif"]
SUPPORTED_VIDEOS = [".mp4", ".mov", ".avi", ".mkv"]


def scan_folder(folder, extensions):
    files = []

    if not folder.exists():
        return files

    for file in folder.iterdir():
        if file.suffix.lower() in extensions:
            files.append({
                "name": file.name,
                "path": str(file),
                "size_mb": round(file.stat().st_size / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(file.stat().st_ctime)
            })

    return sorted(files, key=lambda x: x["created"])


def scan_media():
    photos = scan_folder(PHOTO_DIR, SUPPORTED_PHOTOS)
    videos = scan_folder(VIDEO_DIR, SUPPORTED_VIDEOS)

    print("=" * 50)
    print("MEDIA MANAGER")
    print("=" * 50)

    print(f"\nPhotos : {len(photos)}")
    for p in photos:
        print(f"📷 {p['name']} ({p['size_mb']} MB)")

    print(f"\nVideos : {len(videos)}")
    for v in videos:
        print(f"🎥 {v['name']} ({v['size_mb']} MB)")

    return photos, videos


if __name__ == "__main__":
    scan_media()