import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.media_database import DB_FILE, load_database, update_media


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = PROJECT_ROOT / "data" / "posts"


def get_due_posts(db_file=DB_FILE, now: datetime | None = None) -> list[dict]:
    local_now = now or datetime.now()
    due = []
    for item in load_database(db_file):
        if item.get("status") != "scheduled" or item.get("queue") != "publish_at_scheduled_time":
            continue
        scheduled_at = item.get("scheduled_at")
        if not scheduled_at:
            continue
        try:
            scheduled_time = datetime.fromisoformat(scheduled_at)
        except ValueError:
            continue
        if scheduled_time <= local_now:
            due.append(item)
    return sorted(due, key=lambda item: item["scheduled_at"])


def create_post_package(media: dict, posts_dir=POSTS_DIR) -> Path:
    is_reel = media.get("type") == "video"
    media_path = Path(media.get("reel_path") if is_reel else media["path"])
    if not media_path.is_file():
        raise FileNotFoundError(f"Approved media not found: {media_path}")
    if not media.get("caption") or not media.get("hashtags"):
        raise ValueError("Approved post is missing caption or hashtags.")
    if len([tag for tag in media["hashtags"].split() if tag.startswith("#")]) > 5:
        raise ValueError("Approved post has more than 5 hashtags.")

    posts_dir = Path(posts_dir)
    posts_dir.mkdir(parents=True, exist_ok=True)
    package_path = posts_dir / f"scheduled_{media_path.stem}.json"
    package = {
        "media_file": media["file"],
        "caption": media["caption"],
        "hashtags": media["hashtags"],
        "cta": media.get("cta", ""),
        "media_type": "reel" if is_reel else "photo",
        "scheduled_at": media["scheduled_at"],
        "schedule_timezone": media.get("schedule_timezone", "America/Chicago"),
        "status": "ready_to_publish",
    }
    package["video_path" if is_reel else "image_path"] = str(media_path)
    package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    return package_path


def publish_due_posts(
    db_file=DB_FILE,
    now: datetime | None = None,
    posts_dir=POSTS_DIR,
    publisher_factory: Callable | None = None,
    reel_publisher_factory: Callable | None = None,
) -> list[dict]:
    due_posts = get_due_posts(db_file, now)
    if not due_posts:
        return []

    results = []
    for media in due_posts:
        package_path = create_post_package(media, posts_dir)
        update_media(media["file"], db_file=db_file, status="publishing", queue=None)
        try:
            if media.get("type") == "video":
                if reel_publisher_factory is None:
                    from publishers.reel_publisher import ReelPublisher

                    selected_factory = ReelPublisher
                else:
                    selected_factory = reel_publisher_factory
            else:
                if publisher_factory is None:
                    from publishers.social_publisher import SocialPublisher

                    selected_factory = SocialPublisher
                else:
                    selected_factory = publisher_factory
            result = selected_factory().publish(str(package_path))
        except Exception as exc:
            update_media(
                media["file"],
                db_file=db_file,
                status="publish_failed",
                queue="publish_retry",
                publish_error_type=exc.__class__.__name__,
            )
            results.append({"file": media["file"], "status": "publish_failed"})
            continue

        update_media(
            media["file"],
            db_file=db_file,
            status="published",
            queue=None,
            posted=True,
            published_at=datetime.now().isoformat(timespec="seconds"),
            facebook_post_id=result.get("facebook_post_id"),
            instagram_post_id=result.get("instagram_post_id"),
            post_package=str(package_path),
        )
        results.append({"file": media["file"], "status": "published"})
    return results


if __name__ == "__main__":
    due = get_due_posts()
    if not due:
        print("No scheduled posts are due. Nothing was published.")
    else:
        for result in publish_due_posts():
            print(f"{result['file']} -> {result['status']}")
