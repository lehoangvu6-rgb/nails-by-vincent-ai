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

QUALITY_THRESHOLD = 60


def score_image(image_path):
    image_path = Path(image_path)

    try:
        img = Image.open(image_path)
        img.load()

        width, height = img.size
        size_mb = os.path.getsize(image_path) / 1024 / 1024

        score = 100
        reasons = []

        if width < 1080:
            score -= 20
            reasons.append("width_below_1080")

        if height < 1080:
            score -= 20
            reasons.append("height_below_1080")

        if size_mb < 0.3:
            score -= 20
            reasons.append("file_size_too_small")

        score = max(score, 0)

        status = "ready" if score >= QUALITY_THRESHOLD else "rejected"

        if reasons:
            reason = ", ".join(reasons)
        else:
            reason = "quality_passed"

        return {
            "file": image_path.name,
            "resolution": f"{width} x {height}",
            "width": width,
            "height": height,
            "size": round(size_mb, 2),
            "size_mb": round(size_mb, 2),
            "score": score,
            "status": status,
            "reason": reason,
        }

    except Exception as e:
        print(f"Cannot read {image_path}: {e}")

        return {
            "file": image_path.name,
            "resolution": "unknown",
            "width": 0,
            "height": 0,
            "size": 0,
            "size_mb": 0,
            "score": 0,
            "status": "rejected",
            "reason": f"unreadable_image: {e}",
            "error": str(e),
        }


def check_all_images():
    print("=" * 50)
    print("QUALITY CHECKER")
    print("=" * 50)

    if not PHOTO_DIR.exists():
        print("Photo folder not found.")
        return []

    results = []

    for image in PHOTO_DIR.iterdir():
        if not image.is_file():
            continue

        if image.suffix.lower() not in SUPPORTED_PHOTOS:
            continue

        result = score_image(image)
        results.append(result)

        print()
        print(result["file"])
        print(f"Resolution : {result['resolution']}")
        print(f"Size : {result['size_mb']} MB")
        print(f"Quality Score : {result['score']}/100")
        print(f"Status : {result['status'].upper()}")
        print(f"Reason : {result['reason']}")

    if not results:
        print("No supported photos found.")

    return results


if __name__ == "__main__":
    check_all_images()