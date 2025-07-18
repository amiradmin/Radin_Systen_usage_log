import psutil
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from tabulate import tabulate
import jdatetime  # For Persian (Jalali) dates

# Load credentials
load_dotenv(".env")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

TRACKER_FILE = "usage_tracker.json"
COUNTER_FILE = "log_counter.txt"

def load_usage_data():
    if not Path(TRACKER_FILE).exists():
        return {}
    with open(TRACKER_FILE, "r") as f:
        return json.load(f)

def save_usage_data(data):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def update_usage_data():
    now = datetime.now().astimezone()
    today = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y-%m-%d')
    data = load_usage_data()

    if today not in data:
        data[today] = {"used_seconds": 0, "last_check": now.isoformat()}
    else:
        last_check_str = data[today].get("last_check")
        if last_check_str:
            last_check = datetime.fromisoformat(last_check_str)
            delta = now - last_check
            if 0 < delta.total_seconds() < 3600:  # Ignore long gaps
                data[today]["used_seconds"] += int(delta.total_seconds())

        data[today]["last_check"] = now.isoformat()

    save_usage_data(data)
    return data

def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

def get_usage_table_text(data):
    rows = []
    for date, values in sorted(data.items()):
        if isinstance(values, dict):
            used = values.get("used_seconds", 0)
            rows.append([date, format_duration(used)])
    return tabulate(rows, headers=["Date (Persian)", "Usage Time"], tablefmt="grid", stralign="center")

def get_uptime_log():
    boot_time = datetime.fromtimestamp(psutil.boot_time()).astimezone()
    now = datetime.now().astimezone()
    uptime = now - boot_time

    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Convert to Persian dates
    persian_now = jdatetime.datetime.fromgregorian(datetime=now).strftime('%Y-%m-%d %H:%M:%S')
    persian_boot = jdatetime.datetime.fromgregorian(datetime=boot_time).strftime('%Y-%m-%d %H:%M:%S')

    return f"""
Radin's Uptime Report - {persian_now.split()[0]}
--------------------------------------------
Boot Time      : {persian_boot}
Current Time   : {persian_now}
Uptime Duration: {days}d {hours}h {minutes}m {seconds}s
"""

def get_next_log_index():
    if not Path(COUNTER_FILE).exists():
        with open(COUNTER_FILE, "w") as f:
            f.write("1")
        return 1
    with open(COUNTER_FILE, "r+") as f:
        index = int(f.read().strip())
        f.seek(0)
        f.write(str(index + 1))
        f.truncate()
        return index

def send_email(subject, body):
    recipients = [email.strip() for email in TO_EMAIL.split(",") if email.strip()]
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    data = update_usage_data()
    uptime_log = get_uptime_log()
    usage_summary = get_usage_table_text(data)

    email_body = f"{uptime_log}\nDaily Usage Summary:\n{usage_summary}"

    print(email_body)

    log_index = get_next_log_index()
    subject = f"Radin Daily Uptime Log #{log_index}"

    print("Sending email with uptime log and usage summary...")
    send_email(subject, email_body)
    print("Email sent!")
