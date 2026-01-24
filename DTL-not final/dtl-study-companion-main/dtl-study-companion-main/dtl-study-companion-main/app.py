from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
from flask import request, jsonify
import os
import io
from fpdf import FPDF
from PyPDF2 import PdfReader




from ml.predict import get_digital_twin
from ai.chat_ai import generate_ai_reply
from ml.peak_predict import predict_peak_performance

import sqlite3

app = Flask(__name__)
app.secret_key = "dtl-study-companion-secret-key-2026"

# ================= DATABASE =================

def get_db_connection():
    conn = sqlite3.connect("notes.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()


def init_users_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()
init_users_db()
def init_timer_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            study_date TEXT,
            minutes INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_timer_db()


# ================= LOGIN REQUIRED =================

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

# ================= EMOTION LOGIC (🔥 THIS WAS MISSING) =================

def detect_emotion(actual, target):
    if actual < target * 0.5:
        return "Stressed"
    elif actual >= target:
        return "Focused"
    elif actual >= target * 0.8:
        return "Motivated"
    return "Tired"

# ================= DIGITAL TWIN STATE =================

latest_twin_data = {
    "emotion": "Neutral",
    "lag": 0,
    "consistency": 100
}

peak_cache = {
    "peak_result": None,
    "peak_insight": None,
    "peak_recommendation": None,
    "pattern_insight": None
}

chat_context_used = False

# ================= ROOT =================

@app.route("/")
def root():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

# ================= AUTH =================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
                # ================= BEHAVIORAL (PEAK) TWIN =================

        if "peak_mode" in request.form:

            session_length = int(request.form.get("session_length", 0))
            mood = request.form.get("mood", "Neutral")
            time_of_day = request.form.get("time_of_day", "Morning")
            problem = request.form.get("problem", "None")
            coping = request.form.get("coping", "Break")

            peak_result = predict_peak_performance(
                session_length,
                mood,
                time_of_day,
                problem,
                coping
            )

            peak_cache["peak_result"] = peak_result["score"]
            peak_cache["peak_insight"] = peak_result["status"]
            peak_cache["peak_recommendation"] = peak_result["recommendation"]

            conn.close()

            return render_template(
                "digital_twin.html",
                result=None,
                peak_result=peak_cache["peak_result"],
                peak_insight=peak_cache["peak_insight"],
                peak_recommendation=peak_cache["peak_recommendation"],
                pattern_insight=None,
                show_layout=True
            )

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return render_template("signup.html", error="User already exists", show_layout=False)

    return render_template("signup.html", show_layout=False)


@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password", show_layout=False)

    return render_template("login.html", show_layout=False)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= HOME =================

@app.route("/home")
@login_required
def home():
    return render_template("index.html", show_layout=True)

# ================= DASHBOARD =================

@app.route("/dashboard")
@login_required
def dashboard():
    actual = 45
    target = 90
    emotion = detect_emotion(actual, target)

    return render_template(
        "dashboard.html",
        actual=actual,
        target=target,
        emotion=emotion,
        show_layout=True
    )

# ================= EMOTION =================

@app.route("/emotion")
@login_required
def emotion():
    return render_template("emotion.html", show_layout=True)

# ================= HANDWRITING =================

@app.route("/handwriting")
@login_required
def handwriting():
    return render_template("handwriting.html", show_layout=True)

# ================= TIMER =================

@app.route("/timer")
@login_required
def timer():
    return render_template("timer.html", show_layout=True)




# ================= DIGITAL TWIN =================

@app.route("/digital-twin", methods=["GET", "POST"])
@login_required
def digital_twin():
    global latest_twin_data, peak_cache
    # RESET OLD DATA WHEN PAGE OPENS
    if request.method == "GET":

        session.pop("twin_lag", None)
        session.pop("twin_consistency", None)
        session.pop("twin_emotion", None)

        peak_cache["peak_result"] = None
        peak_cache["peak_insight"] = None
        peak_cache["peak_recommendation"] = None

    

    prediction_message = None

    # SAFE DEFAULTS
    result = {"lag": 0, "consistency": 0, "progress": 0}
    daily_minutes = 0
    remaining_minutes = 0
    days_required = 0

    if request.method == "POST":

        mode = request.form.get("mode", "performance")

        # ================= BEHAVIORAL =================
        if mode == "behavioral":

            session_length = int(request.form.get("peak_minutes", 0))
            mood = request.form.get("peak_mood", "Neutral")
            time_of_day = request.form.get("peak_time", "Morning")
            problem = request.form.get("peak_problem", "None")
            coping = request.form.get("peak_coping", "Break")

            peak_result = predict_peak_performance(
                session_length,
                mood,
                time_of_day,
                problem,
                coping
            )

            peak_cache["peak_result"] = peak_result["score"]
            peak_cache["peak_insight"] = peak_result["status"]
            peak_cache["peak_recommendation"] = peak_result["recommendation"]

            return render_template(
                "digital_twin.html",
                result=None,
                peak_result=peak_cache["peak_result"],
                peak_insight=peak_cache["peak_insight"],
                peak_recommendation=peak_cache["peak_recommendation"],
                pattern_insight=None,
                show_layout=True
            )

        # ================= PERFORMANCE =================

        selected_subject = request.form.get("subject", "ALL")
        days_filter = int(request.form.get("days_filter", 1))

        planned_minutes = int(request.form.get("planned", 0))
        planned_sessions = int(request.form.get("sessions", 1))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT COUNT(DISTINCT study_date),
               IFNULL(SUM(minutes), 0)
        FROM study_sessions
        WHERE study_date >= date('now', ?)
        """

        params = [f"-{days_filter-1} day"]

        if selected_subject != "ALL":
            query += " AND subject = ?"
            params.append(selected_subject)

        cursor.execute(query, params)

        row = cursor.fetchone()
        conn.close()

        days = row[0] if row[0] else 1
        actual_minutes = row[1]

        # ===== CALL MODEL FIRST =====
        result = get_digital_twin(
            days,
            planned_minutes,
            planned_sessions,
            actual_minutes
        )

        if not result:
            result = {"lag": 0, "consistency": 0, "progress": 0}

        # ===== PREDICTION LOGIC =====
        daily_study_hours = 2
        daily_minutes = daily_study_hours * 60

        progress_percent = result["progress"]
        remaining_percent = 100 - progress_percent

        remaining_minutes = int((remaining_percent / 100) * planned_minutes)

        if daily_minutes > 0:
            days_required = round(remaining_minutes / daily_minutes, 2)

        lag_minutes = result["lag"]

        lag_hr = lag_minutes // 60
        lag_min = lag_minutes % 60

        prediction_message = (
            f"You are lagging by {lag_hr} hr {lag_min} min. "
            f"If you study {daily_study_hours} hours daily, "
            f"you can complete this in {days_required} days."
        )

        # ===== UPDATE CHAT CONTEXT =====
        session["twin_lag"] = result["lag"]
        session["twin_consistency"] = result["consistency"]

    if result["consistency"] < 50:
        session["twin_emotion"] = "Stressed"
    elif result["consistency"] < 75:
        session["twin_emotion"] = "Tired"
    else:
        session["twin_emotion"] = "Focused"


    return render_template(
        "digital_twin.html",
        result=result,
        prediction_message=prediction_message,
        peak_result=peak_cache["peak_result"],
        peak_insight=peak_cache["peak_insight"],
        peak_recommendation=peak_cache["peak_recommendation"],
        pattern_insight=peak_cache["pattern_insight"],
        show_layout=True
    )




# ================= CHAT =================
@app.route("/chat", methods=["GET"])
@login_required
def chat_page():
    return render_template("chat.html", show_layout=True)

@app.route("/chat", methods=["POST"])
@login_required
def chat_api():

    try:
        data = request.get_json()
        user_message = data.get("message", "")

        emotion = session.get("twin_emotion", "Neutral")
        lag = session.get("twin_lag", 0)
        consistency = session.get("twin_consistency", 0)

        # DIGITAL TWIN QUERY
        if "digital" in user_message.lower() or "analyze" in user_message.lower():

            if lag > 0:
                lag_hr = lag // 60
                lag_min = lag % 60

                reply = (
                    f"Hey 😊 You're slightly behind today.\n"
                    f"About {lag_hr} hr {lag_min} min.\n"
                )

                if consistency >= 70:
                    reply += "But your consistency is good 💪 Just push a bit more!"
                else:
                    reply += "Let’s add one focused 30-minute session 👍"

            else:
                reply = "🔥 You're on track today! Keep this rhythm going!"

        else:
            reply = generate_ai_reply(
                user_message,
                emotion,
                lag,
                consistency,
                peak_cache["peak_insight"],
                peak_cache["peak_recommendation"]
            )

        return jsonify({"reply": reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"reply": "😅 Give me a second, I'm warming up!"})
    

@app.route("/update_twin_session", methods=["POST"])
@login_required
def update_twin_session():

    data = request.json

    session["twin_lag"] = int(data.get("lag", 0))
    session["twin_consistency"] = int(data.get("consistency", 0))
    session["twin_emotion"] = data.get("emotion", "Neutral")

    return jsonify({"status": "ok"})





# ================= NOTES =================

@app.route("/notes")
@login_required
def notes_page():

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY id DESC")
    notes = cursor.fetchall()
    conn.close()

    return render_template("notes.html", notes=notes, show_layout=True)


@app.route("/save_note", methods=["POST"])
@login_required
def save_note():

    topic = request.form.get("topic")
    content = request.form.get("content")

    if topic and content:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO notes (topic, content) VALUES (?, ?)",
            (topic, content)
        )
        conn.commit()
        conn.close()

    return redirect(url_for("notes_page"))
# ================= NOTES EXTRA TABLE =================

def init_highlight_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS highlights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()

init_highlight_db()


# ================= FILE UPLOAD =================

@app.route("/upload_file", methods=["POST"])
@login_required
def upload_file():

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"})

    filename = file.filename
    text = ""

    # -------- TXT FILE --------
    if filename.endswith(".txt"):
        text = file.read().decode("utf-8")

    # -------- PDF FILE --------
    elif filename.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()

    else:
        return jsonify({"error": "Unsupported file type"})

    # -------- SPLIT INTO CHUNKS --------
    chunk_size = 1500
    chunks = [
        text[i:i + chunk_size]
        for i in range(0, len(text), chunk_size)
    ]

    return jsonify({"chunks": chunks})


# ================= SAVE HIGHLIGHT =================

@app.route("/save_highlight", methods=["POST"])
@login_required
def save_highlight():

    data = request.json

    highlight = data.get("highlight")
    source = data.get("source")

    if not highlight:
        return jsonify({"error": "No highlight received"})

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO highlights (content, source)
        VALUES (?, ?)
    """, (highlight, source))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


# ================= EXPORT PDF =================
from flask import Response
@app.route("/export_notes")
@login_required
def export_notes():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM highlights")
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return "No highlights to export"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    for row in rows:
        text = row["content"]
        text = text.encode("ascii", "ignore").decode("ascii")
        pdf.multi_cell(0, 8, text)
        pdf.ln(4)

    pdf_bytes = bytes(pdf.output(dest="S"), "latin-1")

    # ✅ CLEAR TABLE
    cursor.execute("DELETE FROM highlights")
    conn.commit()
    conn.close()

    response = Response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=My_Study_Notes.pdf"

    return response









@app.route('/save_timer', methods=['POST'])
def save_timer():

    data = request.json

    subject = data['subject']
    minutes = data['minutes']
    today = date.today()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
       INSERT INTO study_sessions(subject, study_date, minutes)
VALUES (?, ?, ?)


    """, (subject, str(today), minutes))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})



# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
