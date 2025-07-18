import psutil
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from tabulate import tabulate

# Load credentials
load_dotenv(".env")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

TRACKER_FILE = "usage_tracker.json"

def load_usage_data():
    if not Path(TRACKER_FILE).exists():
        return {}
    with open(TRACKER_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}  # Return empty if file is corrupted or not JSON

def save_usage_data(data):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def update_usage_data():
    now = datetime.now().astimezone()
    today = now.strftime('%Y-%m-%d')
    data = load_usage_data()

    if today not in data:
        data[today] = {"used_seconds": 0, "last_check": now.isoformat()}
    else:
        last_check_str = data[today].get("last_check")
        if last_check_str:
            try:
                last_check = datetime.fromisoformat(last_check_str)
                delta = now - last_check
                if 0 < delta.total_seconds() < 3600:
                    data[today]["used_seconds"] += int(delta.total_seconds())
            except ValueError:
                pass  # if datetime parsing fails, skip

        data[today]["last_check"] = now.isoformat()

    save_usage_data(data)
    return data

def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

def build_usage_table(data):
    rows = []
    for date, values in sorted(data.items()):
        if isinstance(values, dict):
            used = values.get("used_seconds", 0)
            rows.append([date, format_duration(used)])
    return tabulate(rows, headers=["Date", "Usage Time"], tablefmt="grid")

def get_uptime_log():
    boot_time = datetime.fromtimestamp(psutil.boot_time()).astimezone()
    now = datetime.now().astimezone()
    uptime = now - boot_time

    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"""
Radin's Uptime Report - {now.strftime('%Y-%m-%d')}
--------------------------------------------
Boot Time      : {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
Current Time   : {now.strftime('%Y-%m-%d %H:%M:%S')}
Uptime Duration: {days}d {hours}h {minutes}m {seconds}s
"""

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    data = update_usage_data()
    log = get_uptime_log()
    usage_table = build_usage_table(data)

    full_log = log + "\nDaily Usage Summary:\n" + usage_table

    print(full_log)

    print("Sending email with uptime log...")
    send_email("Radin Daily Uptime Log", full_log)
    print("Email sent!")
