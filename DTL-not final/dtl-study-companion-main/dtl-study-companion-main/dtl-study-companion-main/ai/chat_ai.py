def generate_ai_reply(user_message, emotion, lag, consistency, peak_status, peak_insight):

    system_prompt = f"""
You are my friendly AI Study Companion.

Student status:
Emotion: {emotion}
Lag: {lag} minutes
Consistency: {consistency}%
Peak State: {peak_status}
Behavior Insight: {peak_insight}

Rules:
- Talk like a close friend/mentor.
- Use small paragraphs (2–4 lines).
- Do NOT use bullet points.
- Do NOT speak like a robot.
- Be motivating and warm.
- React emotionally to the student mood.
- Add ONE practical suggestion naturally.
- Keep it conversational.
- Avoid technical words.

Reply style example:

"Heyyy 😊  
I see you’re trying to stay consistent and that already says a lot.

You’re doing okay, but let’s push a little more today.  
Try doing one focused 25-minute session and then take a short break — it really helps!"
"""

    import subprocess

    try:
        process = subprocess.Popen(
            ["ollama", "run", "phi"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        prompt = system_prompt + "\nUser: " + user_message + "\nAssistant:"

        output, error = process.communicate(input=prompt, timeout=40)

        if output and output.strip():
            return output.strip()

        print("OLLAMA ERROR:", error)

        return (
            "Hehe 😅 my brain is warming up.\n\n"
            "Give me one second and send that again — I'm here with you 💙"
        )

    except Exception as e:
        print("AI ERROR:", e)

        return (
            "Oops 😵 something glitched.\n\n"
            "Try sending again — I won’t leave you hanging 😊"
        )
