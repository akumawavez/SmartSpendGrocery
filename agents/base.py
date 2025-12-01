import logging

class Agent:
    def __init__(self, name, model=None):
        self.name = name
        self.model = model
        self.logger = logging.getLogger(name)

    def run(self, input_data):
        self.logger.info(f"Agent {self.name} starting with input: {input_data}")
        result = self.execute(input_data)
        self.logger.info(f"Agent {self.name} finished.")
        return result

    def execute(self, input_data):
        raise NotImplementedError("Subclasses must implement execute method")
