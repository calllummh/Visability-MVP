import seaborn as sns # type: ignore
import numpy as np
import matplotlib as plt
import pandas as pd # type: ignore

# Initialize data storage for engagement and message length analysis
engagement_data = []
message_length_data = []

# Reload updated chat files
chat_files = (f"/user csvs/*.csv")

# Reload the user skills data CSV to redefine user_df
user_data_path = "/mnt/data/user_skills_data.csv"
user_df = pd.read_csv(user_data_path)

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

# Merge engagement data with user skill levels
skill_levels = user_df.set_index("Nickname")[["Final Point (2 Weeks)"]].rename(columns={"Final Point (2 Weeks)": "Final Skill Level"})
engagement_skill_df = engagement_df.merge(skill_levels, left_on="User", right_index=True, how="left")

# Merge message length data with user skill levels
message_length_skill_df = message_length_df.merge(skill_levels, left_on="User", right_index=True, how="left")

# Plot correlation between messages sent per day and skill level
plt.figure(figsize=(8, 6))
sns.regplot(x=engagement_skill_df["Message Count"], y=engagement_skill_df["Final Skill Level"], scatter_kws={"alpha": 0.5})
plt.xlabel("Messages Sent Per Day")
plt.ylabel("Final Skill Level")
plt.title("Correlation Between Messages Sent Per Day and Skill Level")
plt.grid(True)
plt.show()

# Plot correlation between message length and skill level
plt.figure(figsize=(8, 6))
sns.regplot(x=message_length_skill_df["Avg Word Count"], y=message_length_skill_df["Final Skill Level"], scatter_kws={"alpha": 0.5})
plt.xlabel("Average Message Length (Words)")
plt.ylabel("Final Skill Level")
plt.title("Correlation Between Message Length and Skill Level")
plt.grid(True)
plt.show()