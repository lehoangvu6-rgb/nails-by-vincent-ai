import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_FILE = PROJECT_ROOT / "data" / "media_database.json"


def load_database(db_file=DB_FILE):
    db_file = Path(db_file)
    if not DB_FILE.exists():
        return []

    try:
        with db_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_database(data, db_file=DB_FILE):
    db_file = Path(db_file)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=db_file.parent, delete=False) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        temp_path = Path(f.name)
    temp_path.replace(db_file)


def add_media(file_name, media_type, file_path, db_file=DB_FILE, **metadata):

    database = load_database(db_file)

    for item in database:
        if item.get("file") == file_name:
            return False

    record = {
        "file": file_name,
        "path": file_path,
        "type": media_type,
        "status": "new",
        "quality": None,
        "caption": "",
        "hashtags": "",
        "posted": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    record.update(metadata)
    database.append(record)

    save_database(database, db_file)
    return True


def update_media(file_name, db_file=DB_FILE, **kwargs):

    database = load_database(db_file)

    for item in database:
        if item.get("file") == file_name:
            item.update(kwargs)
            item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_database(database, db_file)


def show_database():

    database = load_database()

    print("=" * 50)
    print("MEDIA DATABASE")
    print("=" * 50)

    if len(database) == 0:
        print("Database is empty.")
        return

    for item in database:
        print(item)


if __name__ == "__main__":
    show_database()
