from core.base_agent import BaseAgent
from agents.trend_service import TrendService


class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__("Trend Agent")
        self.service = TrendService()

    def run(self) -> list[str]:
        print("Checking nail trends...")

        trends = self.service.get_trends()

        print("Today's trends:")
        for trend in trends:
            print(f"- {trend}")

        return trends