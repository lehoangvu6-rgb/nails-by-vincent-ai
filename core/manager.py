from core.base_agent import BaseAgent


class Manager(BaseAgent):
    def __init__(self):
        super().__init__("Manager")

    def run(self):
        print("Manager is running...")