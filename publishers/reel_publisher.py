import json
import time
from datetime import datetime
from pathlib import Path

import requests

from integrations.facebook_service import FacebookService
from integrations.instagram_service import InstagramService


class ReelPublisher:
    def __init__(self) -> None:
        self.facebook = FacebookService()
        self.instagram = InstagramService()

    def _video_url(self, video_id: str, attempts: int = 20) -> str:
        for _ in range(attempts):
            response = requests.get(
                f"{self.facebook.base_url}/{video_id}",
                params={"fields": "source", "access_token": self.facebook.access_token},
                timeout=30,
            )
            response.raise_for_status()
            source = response.json().get("source")
            if source:
                return source
            time.sleep(3)
        raise TimeoutError("Facebook Reel source URL was not ready in time.")

    def publish(self, post_path: str) -> dict:
        file_path = Path(post_path)
        post = json.loads(file_path.read_text(encoding="utf-8"))
        required = {"caption", "hashtags", "video_path"}
        missing = required - post.keys()
        if missing:
            raise ValueError(f"Reel package is missing fields: {sorted(missing)}")

        description = "\n\n".join(part for part in (post["caption"].strip(), post["hashtags"].strip()) if part)
        facebook_result = self.facebook.publish_reel(post["video_path"], description)
        facebook_id = facebook_result.get("id")
        if not facebook_id:
            raise ValueError("Facebook did not return a Reel ID.")

        post["facebook_post_id"] = facebook_id
        post["status"] = "facebook_published"
        file_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

        video_url = self._video_url(facebook_id)
        instagram_result = self.instagram.publish_reel_from_url(
            video_url=video_url,
            caption=post["caption"],
            hashtags=post["hashtags"],
        )
        instagram_id = instagram_result.get("id")
        if not instagram_id:
            raise ValueError("Instagram did not return a Reel ID.")

        post.update({
            "instagram_post_id": instagram_id,
            "published_at": datetime.now().isoformat(timespec="seconds"),
            "status": "published",
        })
        file_path.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "facebook_post_id": facebook_id,
            "instagram_post_id": instagram_id,
            "status": "published",
            "post_package": str(file_path),
        }
