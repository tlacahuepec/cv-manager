"""Thin AI provider abstraction. Supports Anthropic and Gemini."""

from __future__ import annotations

import os
import re

from scripts.generate import CVError


def ai_complete(prompt: str, max_tokens: int = 1000) -> str:
    """Send a prompt to the configured AI provider and return the text response."""
    provider = os.environ.get("AI_PROVIDER", "anthropic").lower().strip()

    if provider == "anthropic":
        return _anthropic_complete(prompt, max_tokens)
    elif provider == "gemini":
        return _gemini_complete(prompt, max_tokens)
    else:
        raise CVError(f"Unknown AI_PROVIDER: {provider!r}. Use 'anthropic' or 'gemini'.")


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences that models sometimes wrap around JSON."""
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text)
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def _anthropic_complete(prompt: str, max_tokens: int) -> str:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_code_fences(response.content[0].text.strip())


def _gemini_complete(prompt: str, max_tokens: int) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise CVError("GEMINI_API_KEY is not set. Add it to your .env file.")

    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "max_output_tokens": max_tokens,
            "thinking_config": {"thinking_budget": 0},
        },
    )
    if not response.text:
        finish = response.candidates[0].finish_reason if response.candidates else "unknown"
        raise CVError(f"Gemini returned an empty response (finish_reason={finish}).")
    return _strip_code_fences(response.text.strip())


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    provider = os.environ.get("AI_PROVIDER", "anthropic")
    print(f"Testing AI provider: {provider}")
    try:
        result = ai_complete("Say OK", max_tokens=100)
        print(f"Response: {result}")
    except CVError as e:
        print(f"Error: {e}")
        raise SystemExit(1)
