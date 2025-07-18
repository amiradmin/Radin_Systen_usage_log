import psutil
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

# Load credentials from .env
load_dotenv(".env")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

def get_uptime_log():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    now = datetime.now()
    uptime = now - boot_time

    # Format the current date nicely
    current_date_str = now.strftime('%Y-%m-%d')

    log = f"""
Windows Uptime Report - Date: {current_date_str}
----------------------------------------------
Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}
Uptime Duration: {str(uptime).split('.')[0]}  # removes microseconds for clarity
"""
    return log

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL

    # Gmail SMTP server connection
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    log = get_uptime_log()
    print("Sending email with uptime log...")
    send_email("Radin Daily Windows Uptime Log", log)
    print("Email sent!")
