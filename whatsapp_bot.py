import time
import re
import csv
import os
import pandas as pd # type: ignore
import random
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import google.generativeai as genai
import pathlib
import PyPDF2
from datetime import datetime, timedelta

# Configure Gemini AI
genai.configure(api_key="")  # Store API key in an environment variable
model = genai.GenerativeModel("gemini-2.0-flash")

# Define PDF path and extract text
pdf_path = pathlib.Path("Skills Builder Handbook - Final.pdf")

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

pdf_text = extract_text_from_pdf(pdf_path)
admin="george"
global_processed_messages = set()

# ----------------------------- FUNCTIONS ----------------------------- #
def load_employees():
    """Reads the list of employees from 'employees.txt'. Creates the file if missing."""
    if not os.path.exists("employees.txt"):
        with open("employees.txt", "w") as f:
            f.write("solly\n")  # Default employee
    with open("employees.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_employee(name):
    """Appends a new employee to 'employees.txt'."""
    with open("employees.txt", "a") as f:
        f.write(name + "\n")

def close_overlay():
    """Closes the WhatsApp Keyboard Shortcuts overlay by clicking or pressing Escape."""
    try:
        # Check if the overlay is present
        overlay_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Got it') or contains(text(), 'X')]")
        if overlay_button:
            overlay_button.click()
            print("Closed the WhatsApp Keyboard Shortcuts overlay by clicking.")
            time.sleep(2)  # Allow UI to refresh
            return  # Exit function early if successful
    except Exception:
        pass  # No button found, continue with Escape key approach

    try:
        # Press the Escape key to close the overlay as a fallback
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        print("Pressed Escape to close the overlay.")
        time.sleep(2)  # Allow UI to refresh
    except Exception:
        print("No overlay detected or Escape key method failed.")

def send_message(text):
    """Types and sends a message in the active WhatsApp chat, simulating human typing."""
    time.sleep(2)
    active_element = driver.switch_to.active_element
    active_element.send_keys(text)
    active_element.send_keys(Keys.ENTER)

def save_message(nickname, message, date_time, sender="User"):
    """
    Stores both user and bot messages in the user's chat history file with a date and time stamp.
    
    If a message contains multiple lines (separated by '\n'), each line is stored as a separate entry
    with the same timestamp.
    
    - nickname: Employee's nickname (used for chat file name).
    - message: The message content.
    - date_time: The timestamp of the message.
    - sender: Either "User" or "Bot" to distinguish who sent the message.
    """

    try:
        # Define file name based on the employee's nickname
        chat_filename = f"{nickname}_chat.csv"

        # Check if the file exists to determine whether to write headers
        file_exists = os.path.exists(chat_filename)

        # Split the message on newlines to create separate log entries
        message_parts = message.split("\n")

        # Open the file in append mode (ensure newline issues are avoided)
        with open(chat_filename, mode="a", encoding="utf-8", newline="\n") as file:
            writer = csv.writer(file)

            # Write headers if file is newly created
            if not file_exists:
                writer.writerow(["Time Sent", "Sender", "Message Contents"])

            # Append each line as a new message entry
            for part in message_parts:
                if part.strip():  # Ignore empty lines
                    writer.writerow([date_time, sender, part.strip()])
                    print(f"💾 Saved message for {nickname}: '{part.strip()}' at {date_time}")

    except Exception as e:
        print(f"🚨 Error saving message for {nickname}: {e}")

def skills_profiling(full_name, nickname, job_title, stage):
    """Conducts a structured, scored listening skills assessment with a timed user input window."""
    
    # Start chat session with Gemini
    chat = model.start_chat()
    send_message(f"📋 {full_name}, let's start your listening skills assessment. Please answer each question carefully!")

    num_questions = 5  # Number of questions in the assessment
    skill_level = 0  # Track user's total score

    # Gemini prompt: generate high-quality questions based on the PDF framework
    chat.send_message(
        f"You are an {stage} professional soft-skills assessment bot. Generate a *listening skills assessment* "
        f"for hotel employees based on the attached framework: {pdf_text}. "
        f"Use realistic *hospitality workplace scenarios* with each question, with *four answer choices (a, b, c, d)*. "
        f"There will be {num_questions} questions."
        f"Do *not* show the correct answer, I will ask for this in the next prompt. Ask *one question at a time*, waiting for a response before continuing. Write only the question, scenario and a-d choices - nothing else."
    )

    # Ask Gemini for correct answers in advance for scoring
    correct_answers_response = chat.send_message(
        f"Now, please generate *the {num_questions} correct letter answers, which will correlate with your next prompt* (without questions). "
        f"Please *ONLY OUTPUT THE ANSWERS in the format below, no preamble whatsoever :) :*"
        f"Question 1: b, Question 2: d, etc."
    )

    # Extract the correct answer dictionary properly
    correct_answers_text = correct_answers_response.text.strip()
    correct_answers_list = re.split(r", |\n", correct_answers_text)  # Split on comma or newline
    print(f"📌 Split answers: {correct_answers_list}")  # Debugging log

    # Convert correct answers into a dictionary
    correct_answer_dict = {}
    for ans in correct_answers_list:
        if ":" in ans:
            parts = ans.split(":")  # Split "Question X: Y"
            if len(parts) == 2:  # Ensure correct split
                q_num = parts[0].replace("Question ", "").strip()
                answer = parts[1].strip().lower().rstrip(",")
                correct_answer_dict[q_num] = answer


    # Iterate through the questions
    for i in range(1, num_questions + 1):  
        # Get the next question from Gemini
        response = chat.send_message(f"Ask question {i}. Do *not* show the correct answer, ensure it is aligned with the answers you gave in the response above.")
        question_text = response.text.strip()

        send_message(f"📝 *Question {i}/{num_questions}:*\n{question_text}\n\n")

        # Wait for the user's response using the `user_chat_response)` function
        user_reply = user_chat_response(nickname, 120)  # 2-minute timeout
        if user_reply:
            answer = user_reply[0][0].strip().lower()  # Extract message content safely

            # Validate response
            if answer not in ['a', 'b', 'c', 'd']:
                send_message("⚠️ Invalid response. Please reply with *a, b, c, or d*.")
                user_reply = user_chat_response(nickname, 30)  # Give them another chance (30s)

                if user_reply:
                    answer = user_reply[0][0].strip().lower()  # Extract message content again

                    # Check second attempt validity
                    if answer not in ['a', 'b', 'c', 'd']:
                        send_message("⚠️ Invalid response again. Moving to the next question.")
                        answer = "No response"
                else:
                    send_message("⏳ You took too long to respond again. Moving to the next question.")
                    answer = "No response"
        else:
            send_message("⏳ You took too long to respond. Moving on.")
            answer = "No response"

        # ✅ Fix: Remove the redundant loop and match answer correctly to current question `i`
        question_key = str(i)  # Convert current question number to string

        if question_key in correct_answer_dict:
            correct_answer = correct_answer_dict[question_key].strip().lower().rstrip(",")  # ✅ Remove trailing comma

            # Check and compare only the current question `i`
            if answer in ["a", "b", "c", "d"]:  # Ensure answer is valid before comparing
                if answer == correct_answer:
                    print(f"✅ Correct! Q{i}: User answered {answer}, Correct answer: {correct_answer}")
                    skill_level += 3  # Assign 3 points for a correct answer
                else:
                    print(f"❌ Incorrect. Q{i}: User answered {answer}, Correct answer: {correct_answer}")

    # Determine skill level based on score out of 15
    if skill_level >= 12:
        skill_name = "Advanced"
    elif skill_level >= 7:
        skill_name = "Intermediate"
    else:
        skill_name = "Basic"
        
    send_message(f"✅ Assessment complete! Your Listening Skills Level is *{skill_name}* (Score: {skill_level}/15).")

    # Save skill level in CSV
    # After calculating skill_level, update CSV correctly

    # If it's a mid or final assessment, update only that column
    if stage== "mid stage":
        update_skills_csv(full_name, nickname, column="Mid-Point (1 Week)", value=skill_level)

    elif stage== "final stage":
        update_skills_csv(full_name, nickname, column="Final Point (2 Weeks)", value=skill_level)
    else:
        update_skills_csv(full_name, nickname, job_title, skill_level)  # Initial assessment
        print(full_name, nickname, job_title, skill_level)

    generate_daily_task(full_name, nickname, job_title)
    return skill_level  # Return skill level for further processing

def update_skills_csv(full_name, nickname, job_title=None, skill_level=None, column=None, value=None):
    """
    Updates the CSV with the correct skill assessment in the correct cell.
    - If the user does not exist, creates a new row with `full_name`, `job_title`, and `skill_level`.
    - If the user exists, updates the `column` with the new `value`.
    """

    # Load the CSV (or create it if missing)
    try:
        df = pd.read_csv(skills_csv)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Full Name", "Nickname", "Job Title", "Initial Listening Level", "Mid-Point (1 Week)", "Final Point (2 Weeks)"])

    # Check if the user already exists
    if full_name in df["Full Name"].values:
        # Update the existing entry in the specified column
        if column and value is not None:
            df.loc[df["Full Name"] == full_name, column] = value
            print(f"✅ Updated {column} for {full_name} with value: {value}.")
        else:
            print(f"⚠️ No column/value specified for update.")
    else:
        # Create a new entry if the user is not found
        new_row = pd.DataFrame([[full_name, nickname, job_title, skill_level, "", ""]], 
                                columns=["Full Name", "Nickname", "Job Title", "Initial Listening Level", "Mid-Point (1 Week)", "Final Point (2 Weeks)"])
        df = pd.concat([df, new_row], ignore_index=True)
        print(f"✅ Added new user: {full_name} with Nickname {nickname}, Job Title: {job_title} and Initial Skill Level: {skill_level}.")

    # Save the updated CSV
    df.to_csv(skills_csv, index=False)

def clean_whatsapp_message(raw_text):
    """
    Cleans incoming WhatsApp messages by extracting content and timestamp.
    """
    if not raw_text or len(raw_text) < 6:  # Ensure message is long enough
        return None, None

    if raw_text.startswith("tail-in"):
        raw_text = raw_text[7:].strip()  # Remove "tail-in" prefix

    time_part = raw_text[-5:].strip()  # Extract last 5 characters (expected time format HH:MM)

    try:
        datetime.strptime(time_part, "%H:%M")  # Validate time format
    except ValueError:
        print(f"⚠️ Invalid time format in message: {raw_text}")  # Debugging
        return raw_text, datetime.now().strftime("%Y-%m-%d %H:%M")  # Assume entire message if no valid time

    cleaned_message = raw_text[:-10].strip()  # Extract actual message (excluding timestamp)

    today_date = datetime.now().strftime("%Y-%m-%d")
    date_time = datetime.strptime(f"{today_date} {time_part}", "%Y-%m-%d %H:%M")

    return cleaned_message, date_time

def user_chat_response(nickname, wait_period):
    """
    Waits for a new WhatsApp message from the user.
    Continuously checks for a response instead of using time.sleep().
    """
    timeout = time.time() + wait_period  # timeout in case the user does not respond
    last_message_count = len(driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]"))

    print(f"checking messages from {nickname}")

    while time.time() < timeout:
        messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]")
        if len(messages) > last_message_count:  # If a new message appears
            cleaned_message, date_time = clean_whatsapp_message(messages[-1].text)
            save_message(nickname, cleaned_message, date_time, sender="User")
            print(f"{nickname}: {cleaned_message} @{date_time}")
            return cleaned_message, date_time  # Return the latest message text
        
        time.sleep(1)  # Check for new messages every second
    
    return "", ""  # If the timeout expires, return empty

def onboarding(nickname):
    """Onboards a new user, collects details, and initiates skills profiling step by step."""

    send_message("👋 Hello! Welcome to *Visability*, a soft-skills upskilling platform tailored for hotel employees.")
    time.sleep(2)

    send_message("We're using the *Skills Builder Framework* to help you enhance your *Listening skills* for your workplace.")
    time.sleep(2)

    # Step 1: Ask for Full Name
    send_message("Let's start! Please reply with your *full name*.")

    while True:
        output = user_chat_response(nickname, 20)  # Wait for response
        if output:
            full_name = output[0]
            # Ensure the name has at least two words
            if len(full_name.split()) >= 2:
                time.sleep(2)
                break  # Exit loop and return valid full name
            
            send_message("Hmm, that doesn't look like a full name. Please enter your *first and last name*.")
        else:
            send_message("I didn't get that. Please reply with your full name.")
    
    # Step 2: Ask for Job Title
    send_message(f"Thanks, {full_name}! Now, please reply with your *job title*.")
    
    while True:
        output2 = user_chat_response(nickname, 20)  # Wait for response
        if output2:
            job_title = output2[0]
            # Ensure job title is valid (at least one non-empty word)
            if len(job_title.split()) >= 1:
                send_message(f"Nice to meet you *{full_name}*, *{job_title}*. Let's continue!")
                time.sleep(2)
                break  # Exit loop and return job title
            
            send_message("Hmm, that doesn't seem like a valid job title. Please try again (e.g., Receptionist, Housekeeping Manager).")
        else:
            send_message("I didn't get that. Please enter your job title.")

    # Step 3: Determine Initial Skill Level
    send_message("Now, let's determine your starting skill level.")
    skills_profiling(full_name, nickname, job_title, "initial-onboarding stage")

def reminders():
    """Sends a reminder message once a day if the user has not messaged that day."""
    today = datetime.now().strftime("%Y-%m-%d")

    for nickname in employees:
        chat_filename = f"{nickname}_chat.csv"

        # Check if the user's chat history file exists
        if not os.path.exists(chat_filename):
            print(f"⚠️ No chat history for {nickname}. Sending first reminder.")
            last_message_date = None  # Since no chat file exists, they haven't messaged yet.
        else:
            try:
                df_chat = pd.read_csv(chat_filename)
                if df_chat.empty:
                    last_message_date = None  # Empty file means no previous messages
                else:
                    last_message_date = df_chat["Time Sent"].max()  # Get latest message date

            except Exception as e:
                print(f"🚨 Error reading {chat_filename}: {e}")
                last_message_date = None

        # Send a reminder if no messages were sent today
        if last_message_date is None or last_message_date != today:
            reminder_prompt = (
                "Generate a short, friendly reminder encouraging hotel employees "
                "to practice their listening skills at work today. "
                "Let them know they can respond to WhatsApp if they have questions."
            )
            response = model.generate_content(reminder_prompt)

            try:
                # Extract correct response text
                reminder_text = response.text.strip() if response.text else "Keep practicing your listening skills!"

                print(f"📢 Reminder for {nickname}: {reminder_text}")
                send_message(f"📢 Reminder: {reminder_text}")
                
                # Save reminder message in their chat log
                save_message(nickname, reminder_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

            except Exception as e:
                print(f"🚨 Error processing Gemini response: {e}")
                send_message("📢 Reminder: Keep practicing your listening skills!")

def generate_daily_task(full_name, nickname, job_title):
    """
    Generates a tailored workplace learning module in an interactive, step-by-step manner.
    The user will be guided through learning objectives via Q&A, leading to a practical task.
    """
    message1="⏳ Generating your daily workplace learning module..."
    send_message(message1)
    save_message(nickname, message1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    # Load user skills data
    user_data = pd.read_csv("user_skills_data.csv")

    # Find the user's row in the CSV
    user_row = user_data[user_data["Full Name"] == full_name]
    
    if user_row.empty:
        send_message("⚠️ Error: User not found in the system.")
        return full_name, "Error: User not found."

    # Determine learning module
    initial_level = user_row["Initial Listening Level"].values[0]
    mid_point = user_row["Mid-Point (1 Week)"].values[0]

    if not pd.isna(mid_point):  # If mid-assessment completed, use level 10 module
        module_filename = "level10module.txt"
    elif not pd.isna(initial_level):  # If only onboarding completed, use level 5 module
        module_filename = "level5module.txt"
    else:
        send_message("⚠️ Error: No learning level detected.")
        return full_name, "Error: No learning level detected."

    # Read module content
    if os.path.exists(module_filename):
        with open(module_filename, "r", encoding="utf-8") as file:
            module_content = file.read().strip()
    else:
        send_message(f"⚠️ Error: Learning module {module_filename} not found.")
        return full_name, f"Error: {module_filename} not found."

    # Start interactive conversation
    chat = model.start_chat()
    
    message2=f"📋 {full_name}, today we’ll be focusing on *listening skills* tailored for your role as a {job_title}. Let's go step by step!"
    send_message(message2)
    save_message(nickname, message2, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    # Step 1: Introduction and Learning Objective
    intro_response = chat.send_message(
        f"Summarise the key learning aims from this module:\n\n{module_content}\n\n"
        f"Keep it concise and engaging. Output *only the summary*."
    )
    message3=f"🎯 *Today's Learning Focus:* \n{intro_response.text.strip()}"
    send_message(message3)
    save_message(nickname, message3, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    # Step 2: Engage the User with a Question
    message4="💡 Before we dive in, let’s reflect: In your experience, what do you think makes a great listener at work?"
    send_message(message4)
    save_message(nickname, message4, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
    
    user_reply = user_chat_response(nickname, 120)  # Wait for a response (2 min timeout)
    if not user_reply:
        message5="⏳ No response received! No worries, let's keep going."
        send_message(message5)
        save_message(nickname, message5, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
        user_reply=""

    # Step 3: Break Down Key Concepts
    concept_response = chat.send_message(
        f"Refer to the user's answer (if not empty) to your question ({message4}) as the first part of your response: {user_reply}"
        f"Break down the core principles of *effective listening* from this module into *three simple key points* "
        f"in a way that feels interactive. Keep it step-by-step and engaging."
    )
    message6=f"📖 *Key Concepts:* \n{concept_response.text.strip()}"
    send_message(message6)
    save_message(nickname, message6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    message7="🤔 Which of these do you think you already do well? And which one do you struggle with?"
    send_message(message7)
    save_message(nickname, message7, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
    
    user_reply = user_chat_response(nickname, 120)  # Wait for a response
    if not user_reply:
        message8="⏳ No response received! No worries, let's move on."
        send_message(message8)
        save_message(nickname, message8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
        user_reply=""

    # Step 4: Scenario-Based Question
    scenario_response = chat.send_message(
        f"Refer to the user's answer (if not empty) to your question ({message7}) as the first part of your response: {user_reply}"
        f"Generate a *realistic workplace scenario* testing a listening skill from this module. "
        f"Give four answer choices (a, b, c, d) but do not reveal the correct answer."
    )
    send_message(f"📝 *Scenario:* \n{scenario_response.text.strip()}\n\nReply with *a, b, c,* or *d*.")

    user_reply = user_chat_response(nickname, 120)  # Wait for response
    if user_reply:
        user_answer = user_reply[0][0].strip().lower()
        if user_answer not in ['a', 'b', 'c', 'd']:
            send_message("⚠️ Invalid response. Please reply with *a, b, c,* or *d*.")
            user_reply = user_chat_response(nickname, 30)  # Give another chance (30s)

            if user_reply:
                user_answer = user_reply[0][0].strip().lower()
                if user_answer not in ['a', 'b', 'c', 'd']:
                    message8="⏳ No response received! No worries, let's move on."
                    send_message(message8)
                    save_message(nickname, message8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
                    user_answer = "No response"
            else:
                message8="⏳ No response received! No worries, let's move on."
                send_message(message8)
                save_message(nickname, message8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
                user_answer = "No response"
    else:
        message8="⏳ No response received! No worries, let's move on."
        send_message(message8)
        save_message(nickname, message8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")
        user_answer = "No response"

    # Step 5: Provide Correct Answer & Explanation
    correct_response = chat.send_message(
        f"Now provide the *correct answer* and a *short explanation* for the previous question."
    )
    message9=f"✅ *Correct Answer & Explanation:* \n{correct_response.text.strip()}"
    send_message(message9)
    save_message(nickname, message9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    # Step 6: Assign a Practical Task
    task_response = chat.send_message(
        f"Based on this module, generate a *simple, actionable task* that the employee should complete over the next few days "
        f"to improve their listening skills in the workplace. Keep it realistic and engaging."
    )
    task_text = task_response.text.strip() if task_response.text else "No task generated."

    message10=f"📌 *Your Task for the Next Few Days:* \n{task_text}"
    send_message(message10)
    save_message(nickname, message10, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    # Final Encouragement
    message11="💬 Let me know how it goes! I’m always here to help. 😊"
    send_message(message11)
    save_message(nickname, message11, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

    return full_name, task_text

def user_response(nickname, wait_period):
    """
    Scrapes WhatsApp Web for the latest unread messages, stopping at the most recent already recorded message.
    Returns a single concatenated response string.
    """
    timeout = time.time() + wait_period
    print(f"👂 Listening for messages from {nickname}...")

    all_new_messages = []  # Stores new messages
    csv_file = f"{nickname}_chat.csv"

    # Load chat history CSV once
    try:
        chat_data = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"🚨 {csv_file} not found. Assuming all messages are new.")
        chat_data = None  # If CSV is missing, treat all messages as new

    while time.time() < timeout:
        try:
            # Get all user messages in the chat
            messages = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]")

            if not messages:
                time.sleep(1)  # Avoid tight loops
                continue  # No messages found, keep waiting

            # Iterate from newest to oldest
            for message_element in reversed(messages):
                raw_text = message_element.text.strip()
                
                if not raw_text:
                    continue  # Skip empty messages
                
                cleaned_message, date_time = clean_whatsapp_message(raw_text)

                # Check if the message already exists in the CSV
                if chat_data is not None:
                    message_exists = (
                        (chat_data["Time Sent"] == date_time) & 
                        (chat_data["Sender"] == "User") & 
                        (chat_data["Message Contents"] == cleaned_message)
                    ).any()
                else:
                    message_exists = False  # If no CSV, assume it's new

                if message_exists:
                    print(f"✅ Found latest recorded message: '{cleaned_message}'. Stopping search.")
                    break  # Stop iterating when we reach the first already recorded message

                # If it's a new message, add it to the list
                if cleaned_message not in all_new_messages:
                    all_new_messages.append((cleaned_message, date_time))

            # If new messages were found, reverse the list before saving
            if all_new_messages:
                all_new_messages.reverse()  # Ensure messages are stored from oldest → newest

                for cleaned_message, date_time in all_new_messages:
                    save_message(nickname, cleaned_message, date_time, sender="User")
                    print(f"📩 {nickname}: {cleaned_message} @{date_time}")

                # Concatenate messages for response
                combined_message = " ".join([msg[0] for msg in all_new_messages])
                print(f"📢 Responding to: '{combined_message}'")
                return combined_message

        except Exception as e:
            print(f"⚠️ Error checking for new messages: {e}")

        time.sleep(1)  # Check for new messages every second

    print("⏰ Timeout reached. No new messages detected.")
    return ""  # If timeout expires, return empty

def chat_bot():
    """Checks employee messages and responds accordingly."""
    global employees  # Ensure employees list updates dynamically
    
    for nickname in employees:
        try:
            close_overlay()  # Ensure no overlays block interactions

            # Search for the user in WhatsApp Web
            search_box = driver.find_element(By.XPATH, "//div[@contenteditable='true']")
            search_box.click()
            search_box.send_keys(Keys.COMMAND, "a")
            search_box.send_keys(Keys.DELETE)
            time.sleep(1)
            search_box.send_keys(nickname)
            time.sleep(2)

            chat = driver.find_element(By.XPATH, f"//span[@title='{nickname}']")
            chat.click()
            time.sleep(2)

            # Find the full name and job title from the CSV
            try:
                df = pd.read_csv(skills_csv)
                user_row = df[df["Full Name"].str.contains(nickname, case=False, na=False)]
                
                if not user_row.empty:
                    full_name = user_row.iloc[0]["Full Name"]
                    job_title = user_row.iloc[0]["Job Title"]
                else:
                    print(f"⚠️ No record found for {nickname} in skills CSV.")
                    onboarding(nickname)
                    continue

            except FileNotFoundError:
                print("⚠️ Skills CSV file not found.")
                continue
            
            cleaned_message = user_response(nickname, 20)  # Get newest message

            if cleaned_message:
                if nickname.lower() == admin and cleaned_message.lower().startswith("register "):
                    new_employee = cleaned_message[9:].strip()  # Extract name after "register "
                    
                    if new_employee and new_employee not in employees:
                        employees.append(new_employee)
                        save_employee(new_employee)
                        send_message(f"✅ {new_employee} has been registered as an employee!")
                        print(f"🆕 Added new employee: {new_employee}")
                    else:
                        send_message("⚠️ Employee name missing or already registered.")
                    
                    continue  # Skip to next user

                # Handle special commands for assessments
                if cleaned_message.lower() == "mid assessment":
                    skills_profiling(full_name, nickname, job_title, "mid stage")
                elif cleaned_message.lower() == "final assessment":
                    skills_profiling(full_name, nickname, job_title, "final stage")
                else:
                    # Retrieve last 5 chat messages instead of full history
                    chat_filename = f"{full_name}_chat.csv"
                    chat_history = []
                    if os.path.exists(chat_filename):
                        with open(chat_filename, "r", newline="") as file:
                            chat_lines = file.readlines()[-10:]  # Get last 10 lines
                            chat_history = "".join(chat_lines)
                    else:
                        chat_history = ""

                    # Generate a response using past conversation (Synchronous Execution)
                    prompt = (
                        f"You are a professional soft-skills assessment WhatsApp chatbot (ensure correct formatting for WhatsApp). "
                        f"Be *friendly, conversational, and as concise as possible*. "
                        f"Give a helpful response tailored to {full_name}, {job_title}, "
                        f"refer to the *following framework*: {pdf_text}. "
                        f"\n and the bot/employee's recent chat history:\n{chat_history}\n"
                        f"\nin response to their latest message: '{cleaned_message}'"
                    )

                    response = model.generate_content(prompt)
                    bot_reply = response.text.strip()

                    # Send bot response and save it to the chat log
                    send_message(bot_reply)
                    save_message(nickname, bot_reply, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sender="Bot")

            else:
                if now.hour >= 9 and now.hour <= 11 and now >= reminder_time:
                    reminders()
                    print("✅ Reminders sent successfully!")

                    # Set the next reminder for the next morning
                    reminder_time = now + timedelta(days=1)
                    reminder_time = reminder_time.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
                    print(f"⏳ Next reminder scheduled for {reminder_time.strftime('%Y-%m-%d %H:%M')}")
                continue

        except Exception as e:
            print(f"🚨 Could not process {nickname}: {e}")

# ----------------------------- MAIN LOOP ----------------------------- #
# Load employees initially
employees = load_employees()
print(f"👥 Loaded employees: {employees}")

# Define CSV files
skills_csv = "user_skills_data.csv"

# Ensure user_skills_data CSVs exist
if not os.path.exists(skills_csv):
    with open(skills_csv, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Full Name", "Nickname", "Job Title", "Initial Listening Level", "Mid-Point (1 Week)", "Final Point (2 Weeks)"])

# Start Safari WebDriver
driver = webdriver.Safari()
driver.get("https://web.whatsapp.com")

# Wait for WhatsApp Web login
print("Waiting for WhatsApp Web to log in...")
WebDriverWait(driver, 600).until(
    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
)
print("Login detected. Starting chatbot.")

random_hour = random.randint(9, 11)
random_minute = random.randint(0, 59)
reminder_time = datetime.now().replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)

while True:
    now = datetime.now()
    chat_bot()
    close_overlay()  # Ensure no overlays block interactions
    time.sleep(20)  # Reduce CPU load