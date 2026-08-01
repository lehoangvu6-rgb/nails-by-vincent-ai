import base64
from datetime import datetime
from pathlib import Path

from core.base_agent import BaseAgent
from integrations.openai_service import OpenAIService


class ImageGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Image Generator Agent")
        self.ai = OpenAIService()

        self.output_folder = Path("images/generated")
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def run(self, image_prompt: str) -> str:
        print("Generating nail image...")

        response = self.ai.client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            size="1024x1024",
            quality="high",
        )

        image_base64 = response.data[0].b64_json

        if not image_base64:
            raise ValueError("OpenAI did not return image data.")

        image_bytes = base64.b64decode(image_base64)

        file_name = datetime.now().strftime(
            "nails_by_vincent_%Y%m%d_%H%M%S.png"
        )

        file_path = self.output_folder / file_name
        file_path.write_bytes(image_bytes)

        print(f"Generated image saved at: {file_path}")

        return str(file_path)