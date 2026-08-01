from core.base_agent import BaseAgent
from integrations.openai_service import OpenAIService


class ImagePromptAgent(BaseAgent):
    def __init__(self):
        super().__init__("Image Prompt Agent")
        self.ai = OpenAIService()

    def run(self, caption: str):
        print("Generating image prompt...")

        prompt = f"""
You are an expert AI image prompt engineer.

Create one realistic luxury nail photography prompt.

Caption:
{caption}

Requirements:
- luxury nail salon
- photorealistic
- elegant female hand
- premium lighting
- Instagram quality
- highly detailed

Return only the prompt.
"""

        image_prompt = self.ai.ask(prompt)

        print("\nGenerated Image Prompt:\n")
        print(image_prompt)

        return image_prompt