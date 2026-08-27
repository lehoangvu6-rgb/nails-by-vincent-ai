import json

from core.media_database import add_media, load_database, update_media


def test_database_add_reject_duplicate_and_update(tmp_path):
    db_file = tmp_path / "media.json"

    assert add_media("nails.webp", "photo", "media/photos/nails.webp", db_file=db_file)
    assert not add_media("nails.webp", "photo", "media/photos/nails.webp", db_file=db_file)

    update_media("nails.webp", db_file=db_file, status="ready", quality=90)
    records = load_database(db_file)

    assert len(records) == 1
    assert records[0]["status"] == "ready"
    assert records[0]["quality"] == 90
    assert json.loads(db_file.read_text(encoding="utf-8")) == records


def test_invalid_database_is_treated_as_empty(tmp_path):
    db_file = tmp_path / "media.json"
    db_file.write_text("not-json", encoding="utf-8")

    assert load_database(db_file) == []
