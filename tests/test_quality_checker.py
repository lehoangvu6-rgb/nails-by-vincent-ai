from PIL import Image

from core.quality_checker import score_image


def test_large_image_is_ready(tmp_path):
    image_path = tmp_path / "large.png"
    Image.new("RGB", (1200, 1200), "white").save(image_path)
    result = score_image(image_path)
    assert result["status"] == "ready"
    assert result["score"] >= 60


def test_small_image_is_rejected(tmp_path):
    image_path = tmp_path / "small.jpg"
    Image.new("RGB", (300, 300), "white").save(image_path)
    result = score_image(image_path)
    assert result["status"] == "rejected"


def test_broken_image_is_rejected(tmp_path):
    image_path = tmp_path / "broken.jpg"
    image_path.write_bytes(b"not an image")
    result = score_image(image_path)
    assert result["status"] == "rejected"
    assert result["reason"].startswith("unreadable_image")
