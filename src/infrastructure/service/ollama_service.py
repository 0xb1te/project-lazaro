# src/infrastructure/service/ollama_service.py
import logging
import time
import requests
from typing import List, Dict, Any, Optional
import json

from langchain_ollama import OllamaLLM
from src.domain.port.service.llm_service import LLMService

class OllamaService(LLMService):
    """
    Ollama-based implementation of the LLMService interface using LangChain.
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
            base_url: Base URL of the Ollama API (e.g., "http://172.17.0.1:11434")
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
        
        # Check if Ollama is available during initialization
        self._check_ollama_availability()
    
    def _check_ollama_availability(self):
        """
        Check if Ollama server is available and log appropriate messages.
        """
        try:
            # Try a simple health check
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.logger.info(f"Ollama server is available at {self.base_url}")
            else:
                self.logger.warning(f"Ollama server returned status code {response.status_code} at {self.base_url}")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Could not connect to Ollama server at {self.base_url}: {str(e)}")
    
    def _get_ollama_client(self):
        """
        Create and return a new OllamaLLM client.
        """
        self.logger.info(f"Opened new Ollama client at {self.base_url}, model name: {self.model_name} and timeout settings at: {self.timeout}")
        
        ollamaLLM = OllamaLLM(
            model=self.model_name,
            base_url=self.base_url,
            num_ctx=self.max_tokens,
            temperature=self.temperature,
            request_timeout=self.timeout
        )
        
        return ollamaLLM
    
    def _get_fallback_response(self, question: str) -> str:
        """
        Generate a fallback response when Ollama is unavailable.
        
        Args:
            question: The user's question
            
        Returns:
            Fallback response
        """
        return (
            "I apologize, but I'm currently unable to process your request because the language model "
            "service (Ollama) is not available. This could be due to the server being down, a network "
            "issue, or a configuration problem.\n\n"
            "Here are some steps that might help:\n"
            "1. Ensure that the Ollama server is running\n"
            "2. Check if the correct model is loaded in Ollama\n"
            "3. Verify that the configuration points to the correct Ollama URL\n"
            "4. Check system resources (memory, CPU) to ensure they are sufficient\n\n"
            "If you're an administrator, please check the logs for more details about the connection error."
        )
    
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
        try:
            # Format conversation history
            formatted_history = ""
            if conversation_history and len(conversation_history) > 0:
                try:
                    # Limit to last 5 messages to avoid context overflow
                    recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                    formatted_history = "Previous conversation:\n"
                    for msg in recent_history:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        formatted_history += f"{role}: {msg['content']}\n\n"
                except Exception as e:
                    self.logger.error(f"Error processing conversation history: {str(e)}")
                    formatted_history = ""
            
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

                7. **Professional Tone**:
                - Use a professional and friendly tone.
                - Avoid jargon unless it is necessary and clearly explained.

                8. **Answer if you the user calls you LAZARO**:
                - Answer without taking into account the provided codebase.
                - If you are called LAZARO, you are free to use information outside the context.

                9. **Preserve Existing Functionality**:
                - When suggesting code changes, always identify and preserve existing functionality.
                - Clearly mark which parts of the code remain unchanged and which parts are modified.
                - If suggesting new code, explain how it integrates with the existing system without breaking current features.
                - When modifying code, include comments explaining the rationale for each change.

                10. **Implementation Guidelines**:
                - Present code modifications as targeted changes rather than complete rewrites when possible.
                - For any suggested changes, explain potential impacts on other parts of the codebase.
                - Provide fallback mechanisms or error handling for any new features.

                {formatted_history}

                Document Context:
                {context}

                Current Question:
                {question}

                Answer:
                """

            self.logger.info(f"Provided data for Question: {str(question)} | context: \n {context} and conversation history: \n {conversation_history}")
            
            # Create a fresh client for each attempt
            llm = self._get_ollama_client()
            
            # Get the answer with timeout handling
            answer = llm.invoke(prompt)
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self._get_fallback_response(question)
    
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
            # Add robust retry logic
            max_retries = 3
            retry_delay = 2  # seconds
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Create a fresh client for each attempt
                    llm = self._get_ollama_client()
                    
                    # Get the answer
                    answer = llm.invoke(prompt)
                    
                    # If we got here, the request succeeded
                    if answer and isinstance(answer, str) and len(answer.strip()) > 0:
                        return answer
                    else:
                        self.logger.warning(f"Empty response from Ollama (attempt {attempt+1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            return "I apologize, but I was unable to generate a response. The language model returned an empty result."
                
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"Error on attempt {attempt+1}/{max_retries}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        self.logger.error(f"Final error after {max_retries} attempts: {str(e)}")
            
            # If we get here, all retries failed
            self.logger.error(f"All {max_retries} attempts failed. Last error: {str(last_error)}")
            return f"I'm sorry, I encountered an error while generating a response. The language model service may be unavailable. Error details: {str(last_error)}"
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"I'm sorry, I encountered an error while generating a response: {str(e)}"
    
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
        
        # Generate response with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
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
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON from response (attempt {attempt+1}/{max_retries}): {str(e)}")
                    
                    if attempt < max_retries - 1:
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Last attempt failed, return error info
                        return {
                            "error": "Failed to generate structured output",
                            "raw_response": response_text,
                            "message": str(e)
                        }
                        
            except Exception as e:
                self.logger.error(f"Error in generate_structured_output (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Last attempt failed, return error info
                    return {
                        "error": "Failed to generate structured output",
                        "message": str(e)
                    }
        
        # This should never be reached due to the returns in the loop,
        # but added as a fallback
        return {
            "error": "Failed to generate structured output after all retry attempts"
        }
    
    def check_model_availability(self) -> bool:
        """
        Check if the language model is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            # First, check if Ollama server is accessible
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                if response.status_code != 200:
                    self.logger.warning(f"Ollama server health check failed: {response.status_code} at {self.base_url}")
                    return False
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Could not connect to Ollama server: {str(e)}")
                return False
            
            # Then check if the model is loaded and responsive
            try:
                llm = self._get_ollama_client()
                # Try a simple prompt to check availability
                result = llm.invoke("hello")
                return result is not None and len(result) > 0
            except Exception as e:
                self.logger.warning(f"Model check failed: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Availability check failed: {str(e)}")
            return False