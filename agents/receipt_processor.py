from agents.base import Agent
from tools.parser import ReceiptParser

class ReceiptProcessingAgent(Agent):
    def __init__(self, model=None):
        super().__init__(name="ReceiptProcessor", model=model)
        self.parser = ReceiptParser()

    def execute(self, file_path):
        # In a real scenario, this would call the LLM to verify extraction
        # For now, we delegate to the tool
        print(f"Processing file: {file_path}")
        raw_items = self.parser.parse(file_path)
        return raw_items
