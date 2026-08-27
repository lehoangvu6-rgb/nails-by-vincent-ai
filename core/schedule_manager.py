from datetime import datetime, time, timedelta

from core.media_database import DB_FILE, load_database, update_media


TIMEZONE_NAME = "America/Chicago"

# Initial engagement windows for a local beauty business. These can later be
# replaced with the Page's own Meta/Instagram audience activity data.
PRIME_SLOTS = (
    (1, time(11, 30)),  # Tuesday lunch window
    (3, time(12, 30)),  # Thursday lunch window
)
REEL_TIME = time(19, 30)


def get_scheduling_queue(db_file=DB_FILE) -> list[dict]:
    return [
        item
        for item in load_database(db_file)
        if item.get("status") == "approved" and item.get("queue") == "scheduling"
    ]


def _next_slots(start: datetime, count: int) -> list[datetime]:
    slots = []
    day = start.date()
    while len(slots) < count:
        for weekday, slot_time in PRIME_SLOTS:
            if day.weekday() != weekday:
                continue
            candidate = datetime.combine(day, slot_time)
            if candidate > start:
                slots.append(candidate)
        day += timedelta(days=1)
    return slots


def _next_reel_slots(start: datetime, count: int, database: list[dict]) -> list[datetime]:
    occupied = {item.get("scheduled_at") for item in database if item.get("scheduled_at")}
    photo_days = sorted(
        {
            datetime.fromisoformat(item["scheduled_at"]).date()
            for item in database
            if item.get("type") == "photo"
            and item.get("status") == "scheduled"
            and item.get("scheduled_at")
        }
    )
    slots = []
    for day in photo_days:
        candidate = datetime.combine(day, REEL_TIME)
        if candidate > start and candidate.isoformat(timespec="minutes") not in occupied:
            slots.append(candidate)
            if len(slots) == count:
                return slots

    day = start.date()
    while len(slots) < count:
        candidate = datetime.combine(day, REEL_TIME)
        if candidate > start and candidate.isoformat(timespec="minutes") not in occupied and candidate not in slots:
            slots.append(candidate)
        day += timedelta(days=1)
    return slots


def schedule_approved_posts(db_file=DB_FILE, now: datetime | None = None) -> list[dict]:
    approved = get_scheduling_queue(db_file)
    if not approved:
        return []

    # `now` and stored schedule times are local Monroe time. The IANA timezone
    # name is saved separately so a future publisher can apply DST correctly.
    start = (now or datetime.now()).replace(tzinfo=None)
    database = load_database(db_file)
    photo_posts = [item for item in approved if item.get("type", "photo") != "video"]
    reel_posts = [item for item in approved if item.get("type") == "video"]
    assignments = list(zip(photo_posts, _next_slots(start, len(photo_posts))))
    assignments += list(zip(reel_posts, _next_reel_slots(start, len(reel_posts), database)))
    scheduled = []

    for media, slot in assignments:
        scheduled_at = slot.isoformat(timespec="minutes")
        update_media(
            media["file"],
            db_file=db_file,
            status="scheduled",
            queue="publish_at_scheduled_time",
            scheduled_at=scheduled_at,
            schedule_timezone=TIMEZONE_NAME,
            schedule_strategy="prime_engagement_window_v1",
        )
        scheduled.append({"file": media["file"], "scheduled_at": scheduled_at})
    return scheduled


if __name__ == "__main__":
    results = schedule_approved_posts()
    if not results:
        print("No approved posts are waiting for scheduling.")
    for result in results:
        print(f"{result['file']} -> {result['scheduled_at']}")
