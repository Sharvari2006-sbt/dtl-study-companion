import pandas as pd
import matplotlib.pyplot as plt

# Load stored daily data
df = pd.read_csv("daily_progress.csv")

# -------------------------------
# GRAPH 1: Ideal vs Actual Progress
# -------------------------------
plt.figure(figsize=(8,5))
plt.plot(df["day"], df["ideal_minutes"], label="Digital Twin (Ideal)", marker="o")
plt.plot(df["day"], df["actual_minutes"], label="Actual Progress", marker="o")

plt.title("Actual Progress vs Digital Twin")
plt.xlabel("Day")
plt.ylabel("Minutes Studied")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# -------------------------------
# GRAPH 2: Consistency Over Time
# -------------------------------
plt.figure(figsize=(8,5))
plt.plot(df["day"], df["consistency"], color="green", marker="o")

plt.title("Consistency Over Time")
plt.xlabel("Day")
plt.ylabel("Consistency (%)")
plt.ylim(0, 100)
plt.grid(True)
plt.tight_layout()
plt.show()
