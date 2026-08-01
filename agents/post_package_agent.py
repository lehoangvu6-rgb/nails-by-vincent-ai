import json
from datetime import datetime
from pathlib import Path

from core.base_agent import BaseAgent


class PostPackageAgent(BaseAgent):
    def __init__(self):
        super().__init__("Post Package Agent")

        self.output_folder = Path("data/posts")
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        trends: list[str],
        caption: str,
        hashtags: str,
        image_prompt: str,
        image_path: str,
    ) -> str:
        print("Creating post package...")

        post_data = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "brand": "Nails By Vincent",
            "platforms": ["facebook", "instagram"],
            "trends": trends,
            "caption": caption,
            "hashtags": hashtags,
            "image_prompt": image_prompt,
            "image_path": image_path,
            "status": "ready_for_review",
        }

        file_name = datetime.now().strftime(
            "post_%Y%m%d_%H%M%S.json"
        )

        file_path = self.output_folder / file_name

        file_path.write_text(
            json.dumps(post_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"Post package saved at: {file_path}")

        return str(file_path)