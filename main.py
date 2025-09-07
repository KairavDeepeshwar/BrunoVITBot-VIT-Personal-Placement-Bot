import os
import base64
import requests
import telebot
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# --------------------
# ENV Variables
# --------------------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # your Telegram user ID
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Gmail API Scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

bot = telebot.TeleBot(BOT_TOKEN)


def gmail_service():
    """Authenticate Gmail API using OAuth2 credentials."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=8080)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_emails():
    """Fetch unread emails from inbox."""
    service = gmail_service()
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], q="is:unread"
    ).execute()
    messages = results.get("messages", [])
    mails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId="me", id=msg["id"]).execute()
        payload = msg_data["payload"]

        headers = payload["headers"]
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")

        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode()
        else:
            data = payload["body"].get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode()

        mails.append({"subject": subject, "body": body})
    return mails


def analyze_with_ollama(text):
    """Send mail body to Ollama and summarize placement info."""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"""
Extract the following placement info from this email:

1. Pre-Placement Talk or Online Test date/time (if not mentioned, assume today)
2. Registration/Form links (if any)
3. Key takeaways
4. Full contents
5. If attachments include roll number 22BAI1160 or name 'Kairav Deepeshwar K', say 'SHORTLISTED ✅', else 'Not shortlisted'

Email Text:
{text}
"""
    }
    r = requests.post(url, json=payload, stream=True)
    result = ""
    for line in r.iter_lines():
        if line:
            part = line.decode()
            if '"response"' in part:
                result += part.split('"response":"')[1].split('"')[0]
    return result.strip()


def main():
    emails = fetch_emails()
    for mail in emails:
        summary = analyze_with_ollama(mail["body"])
        bot.send_message(
            CHAT_ID,
            f"📩 *{mail['subject']}*\n\n{summary}",
            parse_mode="Markdown"
        )


if __name__ == "__main__":
    main()
