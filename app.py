from flask import Flask, render_template, request, jsonify
from ml.predict import get_digital_twin
from ai.chat_ai import generate_ai_reply

app = Flask(__name__)


latest_twin_data = {
    "emotion": "Neutral",
    "lag": 0,
    "consistency": 100
}
chat_context_used = False




# ---------------- Emotion Logic ----------------
def detect_emotion(actual, target):
    if actual < target * 0.5:
        return "Stressed"
    elif actual >= target:
        return "Focused"
    elif actual >= target * 0.8:
        return "Motivated"
    return "Tired"

# ---------------- Routes ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    actual = 45
    target = 90
    emotion = detect_emotion(actual, target)
    return render_template(
        "dashboard.html",
        actual=actual,
        target=target,
        emotion=emotion
    )

@app.route("/digital-twin", methods=["GET", "POST"])
def digital_twin():
    global latest_twin_data,chat_context_used
    result = None

    if request.method == "POST":
        result = get_digital_twin(
            int(request.form["day"]),
            int(request.form["planned"]),
            int(request.form["sessions"]),
            int(request.form["actual"])
        )

        # 🔗 STORE FOR AI
        latest_twin_data["lag"] = result["lag"]
        latest_twin_data["consistency"] = result["consistency"]

        if result["consistency"] < 50:
            latest_twin_data["emotion"] = "Stressed"
        elif result["consistency"] < 75:
            latest_twin_data["emotion"] = "Tired"
        else:
            latest_twin_data["emotion"] = "Focused"

    chat_context_used = False

    return render_template("digital_twin.html", result=result)


@app.route("/chat", methods=["GET"])
def chat_page():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat_api():
    global chat_context_used

    data = request.json
    user_message = data["message"]

    emotion = latest_twin_data["emotion"]
    lag = latest_twin_data["lag"]
    consistency = latest_twin_data["consistency"]

    reply = generate_ai_reply(
        user_message,
        emotion,
        lag,
        consistency,
    )

    chat_context_used = True

    return jsonify({"reply": reply})




# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
