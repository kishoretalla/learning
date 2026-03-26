"""
Run this to see which Gemini models are available for your API key.

Usage:
    GEMINI_API_KEY=your_key_here python3 list_models.py
"""
import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("Set GEMINI_API_KEY env var before running:\n  GEMINI_API_KEY=your_key python3 list_models.py")

client = genai.Client(api_key=api_key)
for m in client.models.list():
    print(m.name)
