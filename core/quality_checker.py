from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener
import os

register_heif_opener()

PHOTO_DIR = Path("media/photos")

SUPPORTED_PHOTOS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
]


def score_image(image_path):
    try:
        img = Image.open(image_path)

        width, height = img.size
        size_mb = os.path.getsize(image_path) / 1024 / 1024

        score = 100

        if width < 1080:
            score -= 20

        if height < 1080:
            score -= 20

        if size_mb < 0.3:
            score -= 20

        score = max(score, 0)

        return {
            "file": image_path.name,
            "resolution": f"{width} x {height}",
            "size": round(size_mb, 2),
            "score": score,
        }

    except Exception as e:
        print(f"Cannot read {image_path.name}: {e}")
        return None


def check_all_images():
    print("=" * 50)
    print("QUALITY CHECKER")
    print("=" * 50)

    if not PHOTO_DIR.exists():
        print("Photo folder not found.")
        return

    found = False

    for image in PHOTO_DIR.iterdir():

        if not image.is_file():
            continue

        if image.suffix.lower() not in SUPPORTED_PHOTOS:
            continue

        found = True

        result = score_image(image)

        if not result:
            continue

        print()
        print(result["file"])
        print(f"Resolution : {result['resolution']}")
        print(f"Size : {result['size']} MB")
        print(f"Quality Score : {result['score']}/100")

    if not found:
        print("No supported photos found.")


if __name__ == "__main__":
    check_all_images()