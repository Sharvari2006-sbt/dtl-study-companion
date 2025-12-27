import subprocess
import os

# CHANGE THIS PATH IF NEEDED
OLLAMA_PATH = r"C:\Users\sharv\AppData\Local\Programs\Ollama\ollama.exe"


def generate_ai_reply(user_message, emotion, lag, consistency):
    """
    Generates empathetic AI reply WITH Digital Twin analysis included.
    """

    system_prompt = f"""
You are an AI Study Companion.

Context:
- User emotion: {emotion}
- Study lag compared to ideal self: {lag} minutes
- Study consistency: {consistency}%

Rules:
1. Respond empathetically and naturally (like a human mentor).
2. ALWAYS include Digital Twin analysis in the same response.
3. Mention lag and consistency in a soft, non-judgmental way.
4. Give 1–2 practical suggestions based on the Digital Twin data.
5. Do NOT sound scripted or robotic.
"""

    result = subprocess.run(
        [OLLAMA_PATH, "run", "phi"],
        input=system_prompt + "\nUser: " + user_message,
        text=True,
        capture_output=True
    )

    return result.stdout.strip()
