
#!/usr/bin/env python3
# llm.py - Provider-agnostic LLM interface 
__author__ = 'Forest Mars for Continuum Software'
__version__ = '0.1'
__all__ = [AnthropicProvider]

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLM(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: str = None,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        pass