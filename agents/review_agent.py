from core.base_agent import BaseAgent
from integrations.openai_service import OpenAIService


class ReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__("Review Agent")
        self.ai = OpenAIService()

    def run(
        self,
        caption: str,
        hashtags: str,
        image_prompt: str,
    ) -> str:

        print("Reviewing post quality...")

        prompt = f"""
You are a senior luxury beauty marketing director.

Review the following content.

Caption:
{caption}

Hashtags:
{hashtags}

Image Prompt:
{image_prompt}

Evaluate:

1. Caption quality (score /10)
2. Hashtag quality (score /10)
3. Image prompt quality (score /10)

Then give a short overall recommendation.

Keep the review under 150 words.
"""

        review = self.ai.ask(prompt)

        print("\nReview Report:\n")
        print(review)

        return review