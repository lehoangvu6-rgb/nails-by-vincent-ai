import re
from pathlib import Path

from core.media_database import DB_FILE, load_database, update_media


DEFAULT_HASHTAGS = (
    "#NailsByVincent #LuxuryNails #NailArt #MonroeLA #LouisianaNails"
)


def _design_name(file_name: str) -> str:
    stem = Path(file_name).stem
    words = re.sub(r"[_-]+", " ", stem)
    words = re.sub(r"\b(?:img|image|photo|dsc)\s*\d*\b", "", words, flags=re.IGNORECASE)
    words = " ".join(words.split()).strip()
    return words if words else "this fresh nail design"


def create_local_draft(media: dict) -> dict:
    design = _design_name(media["file"])
    caption = f"Elevated beauty, flawless detail: {design}. Luxury at your fingertips."
    cta = "Book your appointment with Nails by Vincent today."
    return {
        "caption": caption,
        "hashtags": DEFAULT_HASHTAGS,
        "cta": cta,
        "content_source": "local_template",
        "uses_real_media": True,
        "ai_image_generated": False,
    }


def get_content_queue(db_file=DB_FILE) -> list[dict]:
    return [
        item
        for item in load_database(db_file)
        if item.get("type") == "photo"
        and item.get("status") == "ready"
        and item.get("queue") == "content_generation"
    ]


def process_content_queue(db_file=DB_FILE) -> list[dict]:
    processed = []
    for media in get_content_queue(db_file):
        draft = create_local_draft(media)
        update_media(
            media["file"],
            db_file=db_file,
            **draft,
            status="draft_ready",
            queue="review",
        )
        processed.append({**media, **draft, "status": "draft_ready", "queue": "review"})
    return processed


def get_reel_content_queue(db_file=DB_FILE) -> list[dict]:
    return [
        item
        for item in load_database(db_file)
        if item.get("type") == "video"
        and item.get("status") == "reel_ready"
        and item.get("queue") == "reel_content_generation"
        and item.get("reel_path")
    ]


def process_reel_content_queue(db_file=DB_FILE) -> list[dict]:
    processed = []
    for media in get_reel_content_queue(db_file):
        draft = {
            "caption": "Luxury in motion. Flawless details, designed to be noticed.",
            "hashtags": "#NailsByVincent #LuxuryNails #NailReel #NailArt #MonroeLA",
            "cta": "Book your luxury nail experience with Nails by Vincent.",
            "content_source": "local_reel_template",
            "uses_real_media": True,
            "ai_image_generated": False,
        }
        update_media(
            media["file"],
            db_file=db_file,
            **draft,
            status="reel_draft_ready",
            queue="review",
        )
        processed.append({**media, **draft, "status": "reel_draft_ready", "queue": "review"})
    return processed


if __name__ == "__main__":
    drafts = process_content_queue() + process_reel_content_queue()
    if drafts:
        print(f"Created {len(drafts)} content draft(s) from real media.")
    else:
        print("No ready real photos are waiting for content generation.")
