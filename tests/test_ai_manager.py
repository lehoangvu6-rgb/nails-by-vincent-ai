from unittest.mock import Mock, patch

from core.ai_manager import AIManager


def configure_mock_agents(manager: AIManager) -> None:
    manager.trend_agent.run = Mock(
        return_value=["Chrome nails"]
    )
    manager.content_agent.run = Mock(
        return_value="Luxury nail caption"
    )
    manager.hashtag_agent.run = Mock(
        return_value="#NailsByVincent #MonroeLA"
    )
    manager.image_prompt_agent.run = Mock(
        return_value="Luxury nail image prompt"
    )
    manager.image_generator_agent.run = Mock(
        return_value="images/generated/test.png"
    )
    manager.review_agent.run = Mock(
        return_value="Approved"
    )
    manager.post_package_agent.run = Mock(
        return_value="data/posts/test.json"
    )


def test_auto_publish_disabled(monkeypatch):
    monkeypatch.setenv(
        "AUTO_PUBLISH",
        "false",
    )

    manager = AIManager()
    configure_mock_agents(manager)

    with patch(
        "core.ai_manager.SocialPublisher"
    ) as mock_publisher:
        result = manager.run()

    assert result["auto_publish"] is False
    assert result["publish_result"] is None
    mock_publisher.assert_not_called()


def test_auto_publish_enabled(monkeypatch):
    monkeypatch.setenv(
        "AUTO_PUBLISH",
        "true",
    )

    manager = AIManager()
    configure_mock_agents(manager)

    expected_publish_result = {
        "facebook_post_id": "facebook_123",
        "instagram_post_id": "instagram_123",
        "status": "published",
    }

    with patch(
        "core.ai_manager.SocialPublisher"
    ) as mock_publisher_class:
        mock_publisher = (
            mock_publisher_class.return_value
        )
        mock_publisher.publish.return_value = (
            expected_publish_result
        )

        result = manager.run()

    assert result["auto_publish"] is True
    assert (
        result["publish_result"]
        == expected_publish_result
    )

    mock_publisher.publish.assert_called_once_with(
        "data/posts/test.json"
    )