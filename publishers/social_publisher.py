import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from integrations.facebook_service import FacebookService
from integrations.instagram_service import InstagramService


class SocialPublisher:
    def __init__(self) -> None:
        self.facebook = FacebookService()
        self.instagram = InstagramService()

    def _load_post_package(
        self,
        post_path: str,
    ) -> tuple[Path, dict[str, Any]]:
        file_path = Path(post_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Post package not found: {file_path}"
            )

        post_data = json.loads(
            file_path.read_text(encoding="utf-8")
        )

        required_fields = {
            "caption",
            "hashtags",
            "image_path",
        }

        missing_fields = required_fields - post_data.keys()

        if missing_fields:
            raise ValueError(
                "Post package is missing fields: "
                f"{sorted(missing_fields)}"
            )

        return file_path, post_data

    def _get_facebook_image_url(
        self,
        photo_id: str,
    ) -> str:
        response = requests.get(
            (
                f"{self.facebook.base_url}/"
                f"{photo_id}"
            ),
            params={
                "fields": "images",
                "access_token": (
                    self.facebook.access_token
                ),
            },
            timeout=30,
        )

        response.raise_for_status()
        images = response.json().get("images", [])

        if not images:
            raise ValueError(
                "Facebook did not return an image URL."
            )

        return images[0]["source"]

    def _save_result(
        self,
        file_path: Path,
        post_data: dict[str, Any],
    ) -> None:
        file_path.write_text(
            json.dumps(
                post_data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def publish(
        self,
        post_path: str,
    ) -> dict[str, Any]:
        file_path, post_data = (
            self._load_post_package(post_path)
        )

        caption = post_data["caption"]
        hashtags = post_data["hashtags"]
        image_path = post_data["image_path"]

        print("Publishing to Facebook...")

        facebook_result = self.facebook.publish_photo(
            image_path=image_path,
            caption=caption,
            hashtags=hashtags,
        )

        facebook_post_id = facebook_result.get("id")

        if not facebook_post_id:
            raise ValueError(
                "Facebook did not return a post ID."
            )

        post_data["facebook_post_id"] = (
            facebook_post_id
        )
        post_data["status"] = (
            "facebook_published"
        )

        self._save_result(
            file_path,
            post_data,
        )

        image_url = self._get_facebook_image_url(
            facebook_post_id
        )

        print("Publishing to Instagram...")

        try:
            instagram_result = (
                self.instagram.publish_image(
                    image_url=image_url,
                    caption=caption,
                    hashtags=hashtags,
                )
            )
        except Exception:
            post_data["status"] = (
                "facebook_published_instagram_failed"
            )

            self._save_result(
                file_path,
                post_data,
            )
            raise

        instagram_post_id = instagram_result.get("id")

        if not instagram_post_id:
            raise ValueError(
                "Instagram did not return a post ID."
            )

        post_data["instagram_post_id"] = (
            instagram_post_id
        )
        post_data["published_at"] = (
            datetime.now().isoformat(
                timespec="seconds"
            )
        )
        post_data["status"] = "published"

        self._save_result(
            file_path,
            post_data,
        )

        return {
            "facebook_post_id": facebook_post_id,
            "instagram_post_id": instagram_post_id,
            "post_package": str(file_path),
            "status": "published",
        }