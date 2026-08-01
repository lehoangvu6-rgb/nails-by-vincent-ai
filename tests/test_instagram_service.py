from unittest.mock import Mock, patch

from integrations.instagram_service import InstagramService


def create_service(monkeypatch) -> InstagramService:
    monkeypatch.setenv(
        "META_GRAPH_API_VERSION",
        "v25.0",
    )
    monkeypatch.setenv(
        "META_ACCESS_TOKEN",
        "test_access_token",
    )
    monkeypatch.setenv(
        "INSTAGRAM_ACCOUNT_ID",
        "17841461996425230",
    )

    return InstagramService()


def test_get_account_info(monkeypatch):
    service = create_service(monkeypatch)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "17841461996425230",
        "username": "v1ncent.1991",
    }

    with patch(
        "integrations.instagram_service.requests.get",
        return_value=mock_response,
    ) as mock_get:
        result = service.get_account_info()

    assert result["username"] == "v1ncent.1991"
    mock_response.raise_for_status.assert_called_once()

    mock_get.assert_called_once_with(
        (
            "https://graph.facebook.com/v25.0/"
            "17841461996425230"
        ),
        params={
            "fields": "id,username",
            "access_token": "test_access_token",
        },
        timeout=30,
    )


def test_create_image_container(monkeypatch):
    service = create_service(monkeypatch)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "creation_123"
    }

    with patch(
        "integrations.instagram_service.requests.post",
        return_value=mock_response,
    ) as mock_post:
        creation_id = service.create_image_container(
            image_url="https://example.com/nail.png",
            caption="Luxury nails",
            hashtags="#MonroeLA #NailsByVincent",
        )

    assert creation_id == "creation_123"

    call_data = mock_post.call_args.kwargs["data"]

    assert call_data["caption"] == (
        "Luxury nails\n\n"
        "#MonroeLA #NailsByVincent"
    )


def test_wait_until_ready(monkeypatch):
    service = create_service(monkeypatch)

    mock_response = Mock()
    mock_response.json.return_value = {
        "status_code": "FINISHED"
    }

    with patch(
        "integrations.instagram_service.requests.get",
        return_value=mock_response,
    ):
        service.wait_until_ready(
            creation_id="creation_123",
            max_attempts=1,
            delay_seconds=0,
        )

    mock_response.raise_for_status.assert_called_once()


def test_publish_container(monkeypatch):
    service = create_service(monkeypatch)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "instagram_post_123"
    }

    with patch(
        "integrations.instagram_service.requests.post",
        return_value=mock_response,
    ) as mock_post:
        result = service.publish_container(
            creation_id="creation_123"
        )

    assert result["id"] == "instagram_post_123"

    call_data = mock_post.call_args.kwargs["data"]

    assert call_data["creation_id"] == "creation_123"
    assert call_data["access_token"] == "test_access_token"