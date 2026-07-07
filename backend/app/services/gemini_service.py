"""
Gemini Service Wrapper
Provides a safe, fallback-aware interface to the Google Gemini API.
"""
import os
import time
import asyncio
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# Also try .env.example if .env didn't provide the key
if not os.getenv("GEMINI_API_KEY"):
    env_example = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.example')
    load_dotenv(env_example)

# Global flag to track if Gemini is available
_gemini_available = False
_gemini_model = None


def _init_gemini() -> bool:
    """Initialize Gemini API if the API key is present. Returns True if initialized."""
    global _gemini_available, _gemini_model
    
    if _gemini_available:
        return True
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[GEMINI] API key not found in environment. Gemini features disabled.")
        return False
    
    try:
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        _gemini_available = True
        print("[GEMINI] Initialized successfully.")
        return True
    except Exception as e:
        print(f"[GEMINI] Initialization failed: {e}")
        _gemini_available = False
        return False


def generate_text(
    prompt: str,
    max_retries: int = 1,
    timeout_seconds: int = 5,
    fallback: Optional[str] = None,
) -> Optional[str]:
    """
    Generate text using Gemini API with safe fallback.

    Args:
        prompt: The prompt to send to Gemini.
        max_retries: Number of retries on transient failure.
        timeout_seconds: Request timeout in seconds.
        fallback: Value to return if generation fails.

    Returns:
        Generated text string, or fallback/None if unavailable.
    """
    if not _init_gemini():
        return fallback
    
    for attempt in range(1, max_retries + 1):
        try:
            # Use asyncio timeout to prevent indefinite blocking
            async def _call():
                return _gemini_model.generate_content(prompt)
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're inside an async loop (e.g., FastAPI), run in executor with timeout
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(lambda: loop.run_until_complete(_call()))
                    response = future.result(timeout=timeout_seconds)
            else:
                response = loop.run_until_complete(asyncio.wait_for(_call(), timeout=timeout_seconds))
            
            if response and response.text:
                return response.text.strip()
            return fallback
            
        except asyncio.TimeoutError:
            print(f"[GEMINI] Request timed out after {timeout_seconds}s (attempt {attempt}/{max_retries}).")
        except Exception as e:
            print(f"[GEMINI] Generation failed: {e} (attempt {attempt}/{max_retries}).")
    
    return fallback


def is_available() -> bool:
    """Check if Gemini is initialized and available."""
    return _gemini_available and _gemini_model is not None