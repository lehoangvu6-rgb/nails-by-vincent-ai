from unittest.mock import Mock, patch

import pytest

from integrations.facebook_service import FacebookService


def create_service(monkeypatch) -> FacebookService:
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
        "123456789",
    )
    monkeypatch.setenv(
        "FACEBOOK_PLACE_ID",
        "987654321",
    )

    return FacebookService()


def test_get_page_info(monkeypatch):
    service = create_service(monkeypatch)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "123456789",
        "name": "Nails By Vincent",
    }

    with patch(
        "integrations.facebook_service.requests.get",
        return_value=mock_response,
    ) as mock_get:
        result = service.get_page_info()

    assert result["id"] == "123456789"
    assert result["name"] == "Nails By Vincent"

    mock_response.raise_for_status.assert_called_once()

    mock_get.assert_called_once_with(
        "https://graph.facebook.com/v25.0/123456789",
        params={
            "fields": "id,name",
            "access_token": "test_access_token",
        },
        timeout=30,
    )


def test_publish_photo_with_hashtags_and_place(
    monkeypatch,
    tmp_path,
):
    service = create_service(monkeypatch)

    image_path = tmp_path / "test_nail.png"
    image_path.write_bytes(b"fake image data")

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "facebook_post_123"
    }

    with patch(
        "integrations.facebook_service.requests.post",
        return_value=mock_response,
    ) as mock_post:
        result = service.publish_photo(
            image_path=str(image_path),
            caption="Luxury nails by Vincent",
            hashtags=(
                "#NailsByVincent "
                "#MonroeLA "
                "#NailsCreations"
            ),
        )

    assert result["id"] == "facebook_post_123"
    mock_response.raise_for_status.assert_called_once()

    call_data = mock_post.call_args.kwargs["data"]

    assert call_data["caption"] == (
        "Luxury nails by Vincent\n\n"
        "#NailsByVincent "
        "#MonroeLA "
        "#NailsCreations"
    )
    assert call_data["place"] == "987654321"
    assert call_data["published"] == "true"


def test_publish_photo_missing_file(monkeypatch):
    service = create_service(monkeypatch)

    with pytest.raises(FileNotFoundError):
        service.publish_photo(
            image_path="missing_image.png",
            caption="Test caption",
        )   