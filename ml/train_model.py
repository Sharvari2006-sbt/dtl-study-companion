import pandas as pd
from sklearn.linear_model import LinearRegression
import pickle
import os

# Load dataset
df = pd.read_csv("data.csv")

X = df[["day", "planned_minutes", "sessions"]]
y = df["ideal_minutes"]

model = LinearRegression()
model.fit(X, y)

# Save model inside ml folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), "digital_twin_model.pkl")

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("✅ Digital Twin model trained and saved!")
