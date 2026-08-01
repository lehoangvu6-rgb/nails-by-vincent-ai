import os
from pathlib import Path

from dotenv import load_dotenv

from agents.content_agent import ContentAgent
from agents.hashtag_agent import HashtagAgent
from agents.image_generator_agent import ImageGeneratorAgent
from agents.image_prompt_agent import ImagePromptAgent
from agents.post_package_agent import PostPackageAgent
from agents.review_agent import ReviewAgent
from agents.trend_agent import TrendAgent
from publishers.social_publisher import SocialPublisher


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class AIManager:
    def __init__(self) -> None:
        self.trend_agent = TrendAgent()
        self.content_agent = ContentAgent()
        self.hashtag_agent = HashtagAgent()
        self.image_prompt_agent = ImagePromptAgent()
        self.image_generator_agent = ImageGeneratorAgent()
        self.post_package_agent = PostPackageAgent()
        self.review_agent = ReviewAgent()

        self.auto_publish = (
            os.getenv(
                "AUTO_PUBLISH",
                "false",
            ).strip().lower()
            in {
                "true",
                "1",
                "yes",
                "on",
            }
        )

    def run(self) -> dict:
        print("====================================")
        print("NAILS BY VINCENT AI EMPLOYEE")
        print("====================================")

        trends = self.trend_agent.run()

        caption = self.content_agent.run(trends)

        hashtags = self.hashtag_agent.run(caption)

        image_prompt = self.image_prompt_agent.run(
            caption
        )

        image_path = self.image_generator_agent.run(
            image_prompt
        )

        review = self.review_agent.run(
            caption=caption,
            hashtags=hashtags,
            image_prompt=image_prompt,
        )

        post_path = self.post_package_agent.run(
            trends=trends,
            caption=caption,
            hashtags=hashtags,
            image_prompt=image_prompt,
            image_path=image_path,
        )

        publish_result = None

        if self.auto_publish:
            print(
                "\nAUTO_PUBLISH is enabled."
            )
            print(
                "Publishing to Facebook and Instagram..."
            )

            publisher = SocialPublisher()
            publish_result = publisher.publish(
                post_path
            )
        else:
            print(
                "\nAUTO_PUBLISH is disabled."
            )
            print(
                "Post package is waiting for review."
            )

        print("\nGenerated Image:")
        print(image_path)

        print("\nReview Report:")
        print(review)

        print("\nPost Package:")
        print(post_path)

        if publish_result:
            print("\nPublish Result:")
            print(publish_result)

        print("====================================")
        print("All agents completed.")

        return {
            "trends": trends,
            "caption": caption,
            "hashtags": hashtags,
            "image_prompt": image_prompt,
            "image_path": image_path,
            "review": review,
            "post_path": post_path,
            "auto_publish": self.auto_publish,
            "publish_result": publish_result,
        }