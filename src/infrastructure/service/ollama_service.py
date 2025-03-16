# src/infrastructure/service/ollama_service.py
import logging
import json
import requests
from typing import List, Dict, Any, Optional

from src.domain.port.service.llm_service import LLMService

class OllamaService(LLMService):
    """
    Ollama-based implementation of the LLMService interface.
    Uses a self-hosted Ollama instance to generate responses.
    """
    
    def __init__(
        self, 
        model_name: str, 
        base_url: str, 
        temperature: float = 0.7, 
        max_tokens: int = 2000,
        timeout: int = 120
    ):
        """
        Initialize the Ollama service.
        
        Args:
            model_name: Name of the model to use (e.g., "llama2", "codellama")
            base_url: Base URL of the Ollama API (e.g., "http://localhost:11434")
            temperature: Temperature for generation (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, 
                         question: str, 
                         context: str, 
                         conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response to a question based on context and conversation history.
        
        Args:
            question: The user's question
            context: Relevant context for answering the question
            conversation_history: Optional list of previous messages
            
        Returns:
            Generated response text
        """
        # Format conversation history
        formatted_history = ""
        if conversation_history and len(conversation_history) > 0:
            # Limit to last 5 messages to avoid context overflow
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            formatted_history = "Previous conversation:\n"
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                formatted_history += f"{role}: {msg['content']}\n\n"
        
        # Create prompt template
        prompt = f"""
        You are a helpful assistant named LAZARO. Answer the following question based on the context provided below as 
        if you were a senior developer, making me understand the codebase and how it works. Follow these rules strictly:

        1. **Code Formatting**:
        - Every block of code should be placed between `<code></code>` tags.
        - Use proper indentation and syntax highlighting for readability.

        2. **Code Quality**:
        - Follow SOLID principles.
        - Ensure the code is clean, modular, and easy to maintain.

        3. **Code Review**:
        - Review your code to ensure it is functional and free of errors.
        - Do not share non-working or incomplete code.

        4. **Explanation**:
        - Provide a clear and concise explanation of the code, always specify the name of the file you are talking about.
        - Explain how the code works and why it solves the problem.
        - Use bullet points or numbered lists for step-by-step explanations if necessary.

        5. **Context Awareness**:
        - Use both the document context provided and our conversation history to generate the answer.
        - Maintain continuity with previous responses when appropriate.
        
        6. **Code Compression Awareness**:
        - Note that the code you're analyzing has been compressed to reduce token usage.
        - Some variable names and identifiers might have been shortened.
        - Focus on explaining the structure and logic rather than the specific variable names when appropriate.

        {formatted_history}

        Document Context:
        {context}

        Current Question:
        {question}

        Answer:
        """
        
        # Make request to Ollama API
        try:
            max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                error_msg = f"Error from Ollama API: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                # Only retry on certain status codes that might be temporary
                if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                return f"I'm sorry, I'm having trouble generating a response at the moment. Please try again later."
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request to Ollama API failed: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                self.logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            return f"I'm sorry, I'm having trouble connecting to the language model service. Please try again later."

                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request to Ollama API failed: {str(e)}")
            return f"Error connecting to Ollama service: {str(e)}"
    
    def get_model_name(self) -> str:
        """
        Get the name of the language model.
        
        Returns:
            Model name
        """
        return self.model_name
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters used for the language model.
        
        Returns:
            Dictionary of model parameters
        """
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.base_url
        }
    
    def generate_with_prompt(self, prompt: str) -> str:
        """
        Generate text using a custom prompt.
        
        Args:
            prompt: The prompt to use for generation
            
        Returns:
            Generated text
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                error_msg = f"Error from Ollama API: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return f"Error generating response: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request to Ollama API failed: {str(e)}")
            return f"Error connecting to Ollama service: {str(e)}"
    
    def generate_structured_output(self, 
                                 prompt: str, 
                                 output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured output using a prompt and schema.
        
        Args:
            prompt: The prompt to use for generation
            output_schema: Schema defining the expected output structure
            
        Returns:
            Structured output according to the schema
        """
        # Add the schema to the prompt
        schema_str = json.dumps(output_schema, indent=2)
        structured_prompt = f"""
        {prompt}
        
        Please provide your response in the following JSON format:
        {schema_str}
        
        Ensure your response is valid JSON that matches this schema exactly.
        """
        
        # Generate response
        response_text = self.generate_with_prompt(structured_prompt)
        
        # Extract JSON from the response
        try:
            # Look for JSON within the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                return json.loads(response_text)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse JSON from response")
            return {"error": "Failed to generate structured output", "raw_response": response_text}
    
    def check_model_availability(self) -> bool:
        """
        Check if the language model is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                tags = response.json().get("models", [])
                # Check if our model is in the list
                return any(tag.get("name") == self.model_name for tag in tags)
            return False
        except requests.exceptions.RequestException:
            return False