import psutil
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import json

# Load credentials from .env file
load_dotenv(".env")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

TRACK_FILE = "usage_tracker.json"
USAGE_LIMIT_SECONDS = 5 * 60 * 60  # 5 hours

def get_boot_time():
    return datetime.fromtimestamp(psutil.boot_time()).astimezone()

def load_usage_data():
    if os.path.exists(TRACK_FILE):
        with open(TRACK_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"date": "", "used_seconds": 0, "last_check": ""}

def save_usage_data(data):
    with open(TRACK_FILE, 'w') as f:
        json.dump(data, f)

def update_usage():
    now = datetime.now().astimezone()
    today_str = now.strftime('%Y-%m-%d')
    data = load_usage_data()

    # If it's a new day, reset
    if data["date"] != today_str:
        data = {
            "date": today_str,
            "used_seconds": 0,
            "last_check": now.isoformat()
        }
    else:
        # Calculate how much time passed since last check
        if data["last_check"]:
            last_check = datetime.fromisoformat(data["last_check"])
            delta = now - last_check
            if delta.total_seconds() < 3600:  # avoid huge jumps (e.g., if PC was off)
                data["used_seconds"] += int(delta.total_seconds())

        data["last_check"] = now.isoformat()

    save_usage_data(data)
    return data

def format_duration(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def get_uptime_log():
    now = datetime.now().astimezone()
    boot_time = get_boot_time()
    uptime = now - boot_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    usage_data = update_usage()
    used_today_str = format_duration(usage_data["used_seconds"])
    usage_limit_str = format_duration(USAGE_LIMIT_SECONDS)
    over_limit = usage_data["used_seconds"] > USAGE_LIMIT_SECONDS

    status_line = "⚠️ Over the limit!" if over_limit else "✅ Within allowed time."

    log = f"""
Radin Daily Windows Uptime Log - Date: {now.strftime('%Y-%m-%d')}
--------------------------------------------------------
Boot Time        : {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
Current Time     : {now.strftime('%Y-%m-%d %H:%M:%S')}
Session Uptime   : {days}d {hours}h {minutes}m {seconds}s

Total Usage Today: {used_today_str} / {usage_limit_str}
Status           : {status_line}
"""
    print(log)
    return log

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    log = get_uptime_log()
    print("Sending email with uptime log...")
    send_email("Radin Daily Windows Uptime Log", log)
    print("Email sent!")
