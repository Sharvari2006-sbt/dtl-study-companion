def get_digital_twin(day, planned_minutes, sessions, actual_minutes):
    import pickle
    import os
    import csv

    BASE_DIR = os.path.dirname(__file__)
    MODEL_PATH = os.path.join(BASE_DIR, "digital_twin_model.pkl")
    CSV_PATH = os.path.join(BASE_DIR, "daily_progress.csv")

    # ----------------------------
    # Load trained model
    # ----------------------------
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    # ----------------------------
    # Ideal progress (cumulative)
    # ----------------------------
    # We intentionally use:
    # ideal = day * planned_minutes
    ideal_progress = day * planned_minutes

    # ----------------------------
    # Core calculations
    # ----------------------------
    lag = ideal_progress - actual_minutes
    consistency = round((actual_minutes / ideal_progress) * 100, 2)

    # ----------------------------
    # Load previous day's lag
    # ----------------------------
    previous_lag = None

    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, "r") as file:
            rows = list(csv.reader(file))
            if len(rows) > 1:                 # header + at least 1 data row
                previous_lag = int(rows[-1][5])  # yesterday lag

    # ----------------------------
    # Trend analysis
    # ----------------------------
    if previous_lag is not None:
        lag_trend = lag - previous_lag
        if lag_trend < 0:
            trend_message = "You are catching up with your Digital Twin."
        elif lag_trend > 0:
            trend_message = "You are falling behind your Digital Twin."
        else:
            trend_message = "Your progress is stable."
    else:
        trend_message = "No previous data to compare."

    # ----------------------------
    # Feedback message
    # ----------------------------
    if consistency >= 90:
        feedback = "Excellent consistency. Keep going!"
    elif consistency >= 70:
        feedback = "Good effort. Try to push a little more."
    else:
        feedback = "Low consistency. Stick to a tighter schedule."

    # ----------------------------
    # Catch-up simulation
    # ----------------------------
    extra_minutes = 30

    if lag > 0:
        days_to_catch_up = max(1, int(lag / extra_minutes))
        catchup = (
            f"If you study {extra_minutes} extra minutes daily, "
            f"you can catch up in {days_to_catch_up} days."
        )
    else:
        catchup = "You are already ahead of your Digital Twin!"

    # ----------------------------
    # Save today's data
    # ----------------------------
    write_header = not os.path.exists(CSV_PATH)

    with open(CSV_PATH, "a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow([
                "day", "planned", "actual",
                "sessions", "ideal", "lag", "consistency"
            ])
        writer.writerow([
            day,
            planned_minutes,
            actual_minutes,
            sessions,
            ideal_progress,
            lag,
            consistency
        ])

    # ----------------------------
    # Return result to Flask
    # ----------------------------
    return {
        "ideal": ideal_progress,
        "actual": actual_minutes,
        "lag": lag,
        "consistency": consistency,
        "trend": trend_message,
        "feedback": feedback,
        "catchup": catchup
    }
