import smtplib
from dotenv import load_dotenv
import os

load_dotenv(".env")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    print("Login successful!")
except Exception as e:
    print("Login failed:", e)
