import os
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class InstagramService:
    def __init__(self) -> None:
        self.api_version = os.getenv(
            "META_GRAPH_API_VERSION"
        )
        self.access_token = os.getenv(
            "META_ACCESS_TOKEN"
        )
        self.account_id = os.getenv(
            "INSTAGRAM_ACCOUNT_ID"
        )

        if not self.api_version:
            raise ValueError(
                "META_GRAPH_API_VERSION is missing from .env"
            )

        if not self.access_token:
            raise ValueError(
                "META_ACCESS_TOKEN is missing from .env"
            )

        if not self.account_id:
            raise ValueError(
                "INSTAGRAM_ACCOUNT_ID is missing from .env"
            )

        self.base_url = (
            f"https://graph.facebook.com/"
            f"{self.api_version}"
        )

    def get_account_info(self) -> dict[str, Any]:
        url = f"{self.base_url}/{self.account_id}"

        params = {
            "fields": "id,username",
            "access_token": self.access_token,
        }

        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    def create_image_container(
        self,
        image_url: str,
        caption: str,
        hashtags: str = "",
    ) -> str:
        message_parts = [caption.strip()]

        if hashtags.strip():
            message_parts.append(hashtags.strip())

        full_caption = "\n\n".join(message_parts)

        url = (
            f"{self.base_url}/"
            f"{self.account_id}/media"
        )

        data = {
            "image_url": image_url,
            "caption": full_caption,
            "access_token": self.access_token,
        }

        response = requests.post(
            url,
            data=data,
            timeout=60,
        )

        response.raise_for_status()
        result = response.json()

        creation_id = result.get("id")

        if not creation_id:
            raise ValueError(
                "Instagram did not return a creation ID."
            )

        return creation_id

    def wait_until_ready(
        self,
        creation_id: str,
        max_attempts: int = 10,
        delay_seconds: int = 3,
    ) -> None:
        url = f"{self.base_url}/{creation_id}"

        for _ in range(max_attempts):
            response = requests.get(
                url,
                params={
                    "fields": "status_code,status",
                    "access_token": self.access_token,
                },
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            status_code = result.get("status_code")

            if status_code == "FINISHED":
                return

            if status_code in {
                "ERROR",
                "EXPIRED",
            }:
                raise RuntimeError(
                    "Instagram media processing failed: "
                    f"{result}"
                )

            time.sleep(delay_seconds)

        raise TimeoutError(
            "Instagram media was not ready in time."
        )

    def publish_container(
        self,
        creation_id: str,
    ) -> dict[str, Any]:
        url = (
            f"{self.base_url}/"
            f"{self.account_id}/media_publish"
        )

        data = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }

        response = requests.post(
            url,
            data=data,
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    def publish_image(
        self,
        image_url: str,
        caption: str,
        hashtags: str = "",
    ) -> dict[str, Any]:
        creation_id = self.create_image_container(
            image_url=image_url,
            caption=caption,
            hashtags=hashtags,
        )

        self.wait_until_ready(creation_id)

        return self.publish_container(creation_id)

    def publish_reel_from_url(self, video_url: str, caption: str, hashtags: str = "") -> dict[str, Any]:
        full_caption = "\n\n".join(part for part in (caption.strip(), hashtags.strip()) if part)
        response = requests.post(
            f"{self.base_url}/{self.account_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": full_caption,
                "share_to_feed": "true",
                "access_token": self.access_token,
            },
            timeout=60,
        )
        response.raise_for_status()
        creation_id = response.json().get("id")
        if not creation_id:
            raise ValueError("Instagram did not return a Reel creation ID.")
        self.wait_until_ready(creation_id, max_attempts=30, delay_seconds=5)
        return self.publish_container(creation_id)
