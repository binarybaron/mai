import json
import hashlib
import os
import requests
from typing import Optional
from config import OPENROUTER_API_KEY, MODEL_NAME, OPENROUTER_API_URL, CACHE_FILE


class LLMCache:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache from JSON file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to JSON file"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key from text and model name"""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def get(self, text: str, model: str) -> Optional[str]:
        """Get cached response"""
        cache_key = self._get_cache_key(text, model)
        return self.cache.get(cache_key)

    def set(self, text: str, model: str, response: str):
        """Set cached response"""
        cache_key = self._get_cache_key(text, model)
        self.cache[cache_key] = response
        self._save_cache()


# Global cache instance
_cache = LLMCache()


def call_llm(text: str, system_prompt: str = "", model: str = MODEL_NAME) -> str:
    """
    Call LLM with caching support.

    Args:
        text: The user message to send to the LLM
        system_prompt: Optional system prompt
        model: Model name (defaults to config.MODEL_NAME)

    Returns:
        The LLM's response text
    """
    # Create cache key including system prompt
    cache_input = f"{system_prompt}\n\n{text}" if system_prompt else text

    # Check cache first
    cached_response = _cache.get(cache_input, model)
    if cached_response:
        print(f"[Cache hit for {len(text)} chars]")
        return cached_response

    # Make API call
    print(f"[Calling LLM for {len(text)} chars]")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": text})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        llm_response = result['choices'][0]['message']['content']

        # Cache the response
        _cache.set(cache_input, model, llm_response)

        return llm_response

    except requests.exceptions.RequestException as e:
        raise Exception(f"LLM API call failed: {e}")
