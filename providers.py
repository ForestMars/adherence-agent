#!/usr/bin/env python3
# providers.py - Provides providers
__author__ = 'Forest Mars for Continuum Software'
__version__ = '0.1'
__all__ = [AnthropicProvider]

import os
from anthropic import Anthropic
from llm import LLM

class AnthropicProvider(LLM):
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
    
    def generate(self, messages, system_prompt=None, max_tokens=1000):
        """Call Anthropic API endpoint"""
        
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": api_messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text