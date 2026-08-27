import json

import pytest

from core.media_database import load_database
from core.review_manager import approve_post, get_review_queue, reject_post, revise_post


def _database(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text(
        json.dumps(
            [
                {
                    "file": "nails.jpg",
                    "type": "photo",
                    "status": "draft_ready",
                    "queue": "review",
                    "caption": "Original caption",
                    "hashtags": "#NailsByVincent",
                    "cta": "Book today.",
                    "posted": False,
                }
            ]
        ),
        encoding="utf-8",
    )
    return db_file


def test_approve_moves_post_to_scheduling_without_publishing(tmp_path):
    db_file = _database(tmp_path)
    approve_post("nails.jpg", db_file)
    saved = load_database(db_file)[0]
    assert saved["status"] == "approved"
    assert saved["queue"] == "scheduling"
    assert saved["posted"] is False


def test_reject_requires_reason_and_removes_from_queue(tmp_path):
    db_file = _database(tmp_path)
    with pytest.raises(ValueError):
        reject_post("nails.jpg", " ", db_file)
    reject_post("nails.jpg", "Change the wording", db_file)
    saved = load_database(db_file)[0]
    assert saved["status"] == "content_rejected"
    assert saved["queue"] is None
    assert saved["review_note"] == "Change the wording"


def test_revise_keeps_post_in_review(tmp_path):
    db_file = _database(tmp_path)
    revise_post("nails.jpg", caption="Updated caption", db_file=db_file)
    saved = load_database(db_file)[0]
    assert saved["caption"] == "Updated caption"
    assert saved["hashtags"] == "#NailsByVincent"
    assert saved["status"] == "draft_ready"
    assert saved["queue"] == "review"


def test_revise_rejects_more_than_five_hashtags(tmp_path):
    db_file = _database(tmp_path)
    with pytest.raises(ValueError, match="no more than 5"):
        revise_post(
            "nails.jpg",
            hashtags="#One #Two #Three #Four #Five #Six",
            db_file=db_file,
        )


def test_lists_only_reviewable_posts(tmp_path):
    db_file = _database(tmp_path)
    assert [item["file"] for item in get_review_queue(db_file)] == ["nails.jpg"]
    approve_post("nails.jpg", db_file)
    assert get_review_queue(db_file) == []
