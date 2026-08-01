import mimetypes
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class FacebookService:
    def __init__(self) -> None:
        self.api_version = os.getenv(
            "META_GRAPH_API_VERSION"
        )
        self.access_token = os.getenv(
            "META_ACCESS_TOKEN"
        )
        self.page_id = os.getenv(
            "FACEBOOK_PAGE_ID"
        )
        self.place_id = os.getenv(
            "FACEBOOK_PLACE_ID"
        )

        if not self.api_version:
            raise ValueError(
                "META_GRAPH_API_VERSION is missing from .env"
            )

        if not self.access_token:
            raise ValueError(
                "META_ACCESS_TOKEN is missing from .env"
            )

        if not self.page_id:
            raise ValueError(
                "FACEBOOK_PAGE_ID is missing from .env"
            )

        self.base_url = (
            f"https://graph.facebook.com/"
            f"{self.api_version}"
        )

    def get_page_info(self) -> dict[str, Any]:
        url = f"{self.base_url}/{self.page_id}"

        params = {
            "fields": "id,name",
            "access_token": self.access_token,
        }

        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    def publish_photo(
        self,
        image_path: str,
        caption: str,
        hashtags: str = "",
        place_id: str | None = None,
    ) -> dict[str, Any]:
        file_path = Path(image_path)

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Image not found: {file_path}"
            )

        message_parts = [caption.strip()]

        if hashtags.strip():
            message_parts.append(hashtags.strip())

        message = "\n\n".join(message_parts)

        url = f"{self.base_url}/{self.page_id}/photos"

        data = {
            "caption": message,
            "access_token": self.access_token,
            "published": "true",
        }

        selected_place_id = place_id or self.place_id

        if selected_place_id:
            data["place"] = selected_place_id

        mime_type = (
            mimetypes.guess_type(file_path.name)[0]
            or "application/octet-stream"
        )

        with file_path.open("rb") as image_file:
            files = {
                "source": (
                    file_path.name,
                    image_file,
                    mime_type,
                )
            }

            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=120,
            )

        response.raise_for_status()
        return response.json()