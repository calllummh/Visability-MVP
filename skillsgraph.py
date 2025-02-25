import numpy as np
import matplotlib as plt
import pandas as pd # type: ignore
# Load the uploaded CSV file
file_path = "/mnt/data/user_skills_data.csv"
df = pd.read_csv(file_path)

# Extract relevant columns
time_points = ["Initial Listening Level", "Mid-Point (1 Week)", "Final Point (2 Weeks)"]
time_values = [0, 1, 2]  # Corresponding time points

# Calculate the mean skill levels over time
mean_skill_levels = df[time_points].mean()

# Fit a linear trend line (linear regression)
coefficients = np.polyfit(time_values, mean_skill_levels, 1)  # First-degree polynomial (linear)
trend_line = np.poly1d(coefficients)

# Generate trend line values
trend_values = trend_line(time_values)

# Plot skill progression with trend line
plt.figure(figsize=(12, 6))

# Individual skill progressions
for index, row in df.iterrows():
    skill_levels = row[time_points].values
    label_name = row["Nickname"] if pd.notna(row["Nickname"]) else row["Full Name"]
    plt.plot(time_values, skill_levels, marker='o', linestyle='-', alpha=0.3)  # Reduced opacity for clarity

# Plot mean skill levels
plt.plot(time_values, mean_skill_levels, marker='s', linestyle='-', color='black', label="Mean Skill Level", linewidth=2)

# Plot trend line
plt.plot(time_values, trend_values, linestyle='--', color='red', label="Trend Line", linewidth=2)

# Formatting
plt.xticks(time_values, ["Start", "1 Week", "2 Weeks"])
plt.xlabel("Time")
plt.ylabel("Skill Level")
plt.title("Skill Level Progression Over Time with Trend Line")
plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
plt.grid(True)

# Show plot
plt.show()

# Display trend line equation
coefficients
