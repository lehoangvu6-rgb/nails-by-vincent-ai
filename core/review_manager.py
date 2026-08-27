from datetime import datetime

from core.media_database import DB_FILE, load_database, update_media


REVIEWABLE_STATUSES = {"draft_ready", "reel_draft_ready", "changes_requested"}


def get_review_queue(db_file=DB_FILE) -> list[dict]:
    return [
        item
        for item in load_database(db_file)
        if item.get("queue") == "review"
        and item.get("status") in REVIEWABLE_STATUSES
    ]


def _get_reviewable(file_name: str, db_file=DB_FILE) -> dict:
    item = next(
        (entry for entry in load_database(db_file) if entry.get("file") == file_name),
        None,
    )
    if item is None:
        raise ValueError(f"Media not found: {file_name}")
    if item.get("queue") != "review" or item.get("status") not in REVIEWABLE_STATUSES:
        raise ValueError(f"Media is not waiting for review: {file_name}")
    return item


def approve_post(file_name: str, db_file=DB_FILE) -> None:
    _get_reviewable(file_name, db_file)
    update_media(
        file_name,
        db_file=db_file,
        status="approved",
        queue="scheduling",
        approved_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        review_note="",
    )


def reject_post(file_name: str, reason: str, db_file=DB_FILE) -> None:
    _get_reviewable(file_name, db_file)
    if not reason.strip():
        raise ValueError("A rejection reason is required.")
    update_media(
        file_name,
        db_file=db_file,
        status="content_rejected",
        queue=None,
        rejected_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        review_note=reason.strip(),
    )


def revise_post(
    file_name: str,
    *,
    caption: str | None = None,
    hashtags: str | None = None,
    cta: str | None = None,
    db_file=DB_FILE,
) -> None:
    current = _get_reviewable(file_name, db_file)
    changes = {
        "caption": caption.strip() if caption is not None else current.get("caption", ""),
        "hashtags": hashtags.strip() if hashtags is not None else current.get("hashtags", ""),
        "cta": cta.strip() if cta is not None else current.get("cta", ""),
        "status": "draft_ready",
        "queue": "review",
        "revised_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if not changes["caption"]:
        raise ValueError("Caption cannot be empty.")
    hashtag_count = len([word for word in changes["hashtags"].split() if word.startswith("#")])
    if hashtag_count > 5:
        raise ValueError("Use no more than 5 hashtags per post.")
    update_media(file_name, db_file=db_file, **changes)


if __name__ == "__main__":
    items = get_review_queue()
    print(f"Posts waiting for review: {len(items)}")
    for item in items:
        print(f"- {item['file']}: {item.get('caption', '')}")
