from core.base_agent import BaseAgent
from integrations.openai_service import OpenAIService


class ContentAgent(BaseAgent):
    def __init__(self):
        super().__init__("Content Agent")
        self.ai = OpenAIService()

    def run(self, trends: list[str]):
        print("Creating social media content...")

        trend_text = ", ".join(trends)

        prompt = f"""
You are a luxury nail salon marketing expert.

Today's nail trends:
{trend_text}

Write one Instagram caption under 30 words.
Use today's trends naturally.
Luxury style.
"""

        result = self.ai.ask(prompt)

        print("\nGenerated Caption:")
        print(result)

        return result