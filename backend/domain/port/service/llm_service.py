# src/domain/port/service/llm_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMService(ABC):
    """
    Port (interface) for large language model services.
    This interface defines operations for generating text responses from prompts.
    
    Implementations might use different LLM providers or models.
    """
    
    @abstractmethod
    def generate_response(self, 
                         prompt: Optional[str] = None, 
                         temperature: float = 0.7, 
                         max_tokens: Optional[int] = None,
                         context: Optional[str] = None,
                         question: Optional[str] = None) -> str:
        """
        Generate a text response to a given prompt or question.
        
        Args:
            prompt: The prompt to generate a response for (if provided, overrides question)
            temperature: Controls randomness in generation (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            context: Additional context to consider when generating a response
            question: The question to generate a response for (used if prompt is None)
            
        Returns:
            The generated text response
        """
        pass
    
    @abstractmethod
    def generate_chat_response(self, 
                             messages: List[Dict[str, str]], 
                             temperature: float = 0.7,
                             max_tokens: Optional[int] = None,
                             context: Optional[str] = None) -> str:
        """
        Generate a response in a chat-based conversation.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Controls randomness in generation (0.0-1.0)
            max_tokens: Maximum number of tokens to generate
            context: Additional context to consider when generating a response
            
        Returns:
            The generated response text
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the language model being used.
        
        Returns:
            The model name
        """
        pass
    
    @abstractmethod
    def get_model_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters used for the language model.
        
        Returns:
            Dictionary of model parameters
        """
        pass
    
    @abstractmethod
    def generate_with_prompt(self, prompt: str) -> str:
        """
        Generate text using a custom prompt.
        
        Args:
            prompt: The prompt to use for generation
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def check_model_availability(self) -> bool:
        """
        Check if the language model is available.
        
        Returns:
            True if available, False otherwise
        """
        pass
