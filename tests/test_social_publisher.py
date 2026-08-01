import json
from unittest.mock import Mock, patch

import pytest

from publishers.social_publisher import SocialPublisher


def configure_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "META_GRAPH_API_VERSION",
        "v25.0",
    )
    monkeypatch.setenv(
        "META_ACCESS_TOKEN",
        "test_access_token",
    )
    monkeypatch.setenv(
        "FACEBOOK_PAGE_ID",
        "facebook_page_123",
    )
    monkeypatch.setenv(
        "FACEBOOK_PLACE_ID",
        "facebook_place_123",
    )
    monkeypatch.setenv(
        "INSTAGRAM_ACCOUNT_ID",
        "instagram_account_123",
    )


def test_publish_to_facebook_and_instagram(
    monkeypatch,
    tmp_path,
):
    configure_environment(monkeypatch)

    image_path = tmp_path / "nail.png"
    image_path.write_bytes(b"fake image")

    post_path = tmp_path / "post.json"

    post_path.write_text(
        json.dumps(
            {
                "caption": "Luxury nails",
                "hashtags": (
                    "#NailsByVincent #MonroeLA"
                ),
                "image_path": str(image_path),
                "status": "ready_for_review",
            }
        ),
        encoding="utf-8",
    )

    publisher = SocialPublisher()

    mock_image_response = Mock()
    mock_image_response.json.return_value = {
        "images": [
            {
                "source": (
                    "https://example.com/nail.png"
                )
            }
        ]
    }

    with (
        patch.object(
            publisher.facebook,
            "publish_photo",
            return_value={
                "id": "facebook_post_123"
            },
        ) as mock_facebook,
        patch(
            "publishers.social_publisher.requests.get",
            return_value=mock_image_response,
        ),
        patch.object(
            publisher.instagram,
            "publish_image",
            return_value={
                "id": "instagram_post_123"
            },
        ) as mock_instagram,
    ):
        result = publisher.publish(
            str(post_path)
        )

    assert result["status"] == "published"
    assert (
        result["facebook_post_id"]
        == "facebook_post_123"
    )
    assert (
        result["instagram_post_id"]
        == "instagram_post_123"
    )

    mock_facebook.assert_called_once_with(
        image_path=str(image_path),
        caption="Luxury nails",
        hashtags=(
            "#NailsByVincent #MonroeLA"
        ),
    )

    mock_instagram.assert_called_once_with(
        image_url=(
            "https://example.com/nail.png"
        ),
        caption="Luxury nails",
        hashtags=(
            "#NailsByVincent #MonroeLA"
        ),
    )

    saved_post = json.loads(
        post_path.read_text(encoding="utf-8")
    )

    assert saved_post["status"] == "published"
    assert (
        saved_post["facebook_post_id"]
        == "facebook_post_123"
    )
    assert (
        saved_post["instagram_post_id"]
        == "instagram_post_123"
    )
    assert "published_at" in saved_post


def test_missing_post_package(
    monkeypatch,
):
    configure_environment(monkeypatch)
    publisher = SocialPublisher()

    with pytest.raises(FileNotFoundError):
        publisher.publish(
            "missing_post.json"
        )


def test_missing_required_fields(
    monkeypatch,
    tmp_path,
):
    configure_environment(monkeypatch)
    publisher = SocialPublisher()

    post_path = tmp_path / "invalid.json"

    post_path.write_text(
        json.dumps(
            {
                "caption": "Missing other fields"
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        publisher.publish(
            str(post_path)
        )