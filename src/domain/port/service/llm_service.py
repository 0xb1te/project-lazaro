# src/domain/port/service/llm_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMService(ABC):
    """
    Port (interface) defining operations for large language model services.
    This interface allows the domain and application layers to interact with
    LLM services without knowing the specific implementation.
    
    Implementations of this interface might use Ollama, OpenAI, or other LLM providers.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name or identifier of the language model.
        
        Returns:
            Model name or identifier
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