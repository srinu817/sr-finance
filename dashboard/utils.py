import requests
import threading
from django.conf import settings

def send_user_mail(user, subject, message):
    if not user.email:
        print("❌ No email")
        return

    try:
        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json"
        }

        data = {
            "sender": {
                "name": "SR Finance",
                "email": settings.DEFAULT_FROM_EMAIL
            },
            "to": [{"email": user.email}],
            "subject": subject,
            "textContent": message
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)

        print("📩 STATUS:", response.status_code)
        print("📩 RESPONSE:", response.text)

    except Exception as e:
        print("❌ Email Error:", e)


# 🔥 THREAD FUNCTION
def send_mail_async(user, subject, message):
    threading.Thread(
        target=send_user_mail,
        args=(user, subject, message),
        daemon=True
    ).start()
