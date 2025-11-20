#!/usr/bin/env python3
"""
Quick test script for OpenRouter/Gemini integration.

Usage:
    1. Set OPENROUTER_API_KEY in .env file
    2. Run: python test_openrouter.py
"""

import asyncio
import os
from pathlib import Path

# Load .env if exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

from skills.swarm_core import call_llm_api


async def test_basic_call():
    """Test basic OpenRouter call with simple prompt."""
    print("=" * 60)
    print("Testing OpenRouter/Gemini Integration")
    print("=" * 60)

    # Check if API key is set
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("\n⚠️  OPENROUTER_API_KEY not set or using placeholder")
        print("   Please set your API key in .env file")
        print("   Get your key from: https://openrouter.ai/keys")
        print("\n   Running with mock response for demonstration...")
    else:
        print(f"\n✓ API key found: {api_key[:8]}...{api_key[-4:]}")

    # Create simple test prompt
    test_prompt = """
You are a trading analyst. Analyze this market condition and respond in JSON format:

Market: AAPL at $180, IV Rank: 85%

Respond with:
{
  "signal": "SHORT_PUT_SPREAD",
  "target": "AAPL",
  "params": {
    "strike_short": 175,
    "strike_long": 170,
    "expiry": "20251128"
  },
  "confidence": 0.80,
  "reasoning": "High IV suggests premium selling opportunity"
}
"""

    market_data = {
        "symbols": ["AAPL"],
        "timestamp": "2025-11-20T10:00:00"
    }

    print("\n📤 Sending test prompt to OpenRouter/Gemini...")
    print(f"   Model: google/gemini-2.5-flash")

    try:
        response = await call_llm_api(test_prompt, market_data)

        if response:
            print("\n✅ Response received successfully!")
            print("\n📥 Parsed Response:")
            print(f"   Signal: {response.get('signal')}")
            print(f"   Target: {response.get('target')}")
            print(f"   Confidence: {response.get('confidence')}")
            print(f"   Reasoning: {response.get('reasoning')}")

            if api_key and api_key != "your_openrouter_api_key_here":
                print("\n🎉 OpenRouter integration is working correctly!")
            else:
                print("\n💡 This was a mock response. Set OPENROUTER_API_KEY to test real API.")
        else:
            print("\n❌ Failed to get response from OpenRouter")
            print("   Check your API key and network connection")

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print("   Check error message above for details")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_basic_call())
