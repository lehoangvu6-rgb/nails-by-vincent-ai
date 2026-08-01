from core.base_agent import BaseAgent
from integrations.openai_service import OpenAIService


class HashtagAgent(BaseAgent):
    def __init__(self):
        super().__init__("Hashtag Agent")
        self.ai = OpenAIService()

    def run(self, caption: str):
        print("Generating hashtags...")

        prompt = f"""
Create 15 Instagram hashtags for this luxury nail salon caption.

Caption:
{caption}

Rules:
- Return hashtags only.
- Separate by spaces.
- No explanation.
"""

        hashtags = self.ai.ask(prompt)

        print("\nGenerated Hashtags:")
        print(hashtags)

        return hashtags