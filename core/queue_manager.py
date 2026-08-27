from datetime import datetime


def queue_for(media_type: str, status: str) -> str | None:
    if status in {"duplicate", "rejected"}:
        return None
    if media_type == "video":
        return "video_edit_10s"
    return "content_generation"


def queue_metadata(media_type: str, status: str) -> dict:
    queue = queue_for(media_type, status)
    return {
        "queue": queue,
        "queued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if queue else None,
    }
