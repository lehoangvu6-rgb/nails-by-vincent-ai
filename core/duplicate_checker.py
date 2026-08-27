import hashlib
from pathlib import Path


def calculate_hash(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file_handle:
        while chunk := file_handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicate(content_hash: str, database: list[dict]) -> dict | None:
    return next((item for item in database if item.get("content_hash") == content_hash), None)
