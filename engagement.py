import numpy as np
import matplotlib as plt
import pandas as pd # type: ignore

# Plot engagement (messages per day per user)
plt.figure(figsize=(12, 6))

# Reload updated chat files
chat_files = (f"/user csvs/*.csv")

# Initialize data storage for engagement and message length analysis
engagement_data = []
message_length_data = []

# Process each chat file
for chat_file in chat_files:
    df = pd.read_csv(chat_file)

    # Ensure proper column names
    df.columns = df.columns.str.strip()

    # Extract user name from filename
    user_name = chat_file.split("/")[-1].replace(".csv", "")

    # Filter only user messages
    user_messages = df[df["Sender"] == "User"]

    # Convert time to datetime
    user_messages["Time Sent"] = pd.to_datetime(user_messages["Time Sent"])
    user_messages["Date"] = user_messages["Time Sent"].dt.date

    # Count messages per day
    daily_message_count = user_messages.groupby("Date").size().reset_index(name="Message Count")
    daily_message_count["User"] = user_name
    engagement_data.append(daily_message_count)

    # Compute average message length per day
    user_messages["Word Count"] = user_messages["Message Contents"].apply(lambda x: len(str(x).split()))
    daily_avg_length = user_messages.groupby("Date")["Word Count"].mean().reset_index(name="Avg Word Count")
    daily_avg_length["User"] = user_name
    message_length_data.append(daily_avg_length)

# Combine data
engagement_df = pd.concat(engagement_data, ignore_index=True)
message_length_df = pd.concat(message_length_data, ignore_index=True)


# Plot individual user message counts
for user in engagement_df["User"].unique():
    user_data = engagement_df[engagement_df["User"] == user]
    plt.plot(user_data["Date"], user_data["Message Count"], marker='o', linestyle='-', alpha=0.4, label=user)

# Compute and plot mean message count per day
mean_message_counts = engagement_df.groupby("Date")["Message Count"].mean().reset_index()
plt.plot(mean_message_counts["Date"], mean_message_counts["Message Count"], linestyle='-', color='blue', label="Mean Messages Per Day", linewidth=2)

# Compute and plot trend line for mean message counts
x_values = np.arange(len(mean_message_counts))
trend_coeff = np.polyfit(x_values, mean_message_counts["Message Count"], 1)
trend_line = np.poly1d(trend_coeff)
plt.plot(mean_message_counts["Date"], trend_line(x_values), linestyle='--', color='red', label="Trend Line", linewidth=2)

plt.xlabel("Date")
plt.ylabel("Number of Messages")
plt.title("User Engagement: Messages Sent Per Day")
plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
plt.xticks(rotation=45)
plt.grid(True)
plt.show()

# Plot message length (average word count per day per user)
plt.figure(figsize=(12, 6))

# Plot individual user message lengths
for user in message_length_df["User"].unique():
    user_data = message_length_df[message_length_df["User"] == user]
    plt.plot(user_data["Date"], user_data["Avg Word Count"], marker='o', linestyle='-', alpha=0.4, label=user)

# Compute and plot mean message length per day
mean_message_lengths = message_length_df.groupby("Date")["Avg Word Count"].mean().reset_index()
plt.plot(mean_message_lengths["Date"], mean_message_lengths["Avg Word Count"], linestyle='-', color='blue', label="Mean Word Count Per Day", linewidth=2)

# Compute and plot trend line for mean message length
x_values = np.arange(len(mean_message_lengths))
trend_coeff = np.polyfit(x_values, mean_message_lengths["Avg Word Count"], 1)
trend_line = np.poly1d(trend_coeff)
plt.plot(mean_message_lengths["Date"], trend_line(x_values), linestyle='--', color='red', label="Trend Line", linewidth=2)

plt.xlabel("Date")
plt.ylabel("Average Word Count")
plt.title("User Engagement: Average Message Length Per Day")
plt.legend(loc="upper left", bbox_to_anchor=(1, 1))
plt.xticks(rotation=45)
plt.grid(True)
plt.show()
