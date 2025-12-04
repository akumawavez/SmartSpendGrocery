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
    
    def call_llm(self, prompt, system_prompt=None):
        """
        Call the LLM model with a prompt
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system prompt for context
            
        Returns:
            LLM response text
        """
        if self.model is None:
            raise ValueError(f"Agent {self.name} does not have a model configured")
        
        try:
            # Combine system prompt and user prompt if system prompt provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Error calling LLM: {str(e)}")
            raise