from openai import OpenAI
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def query_perplexity(client: OpenAI, query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to give concise answers."
            ),
        },
        {"role": "user", "content": query},
    ]
    print(f"[Perplexity API] Query: {query}")
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )
    print(f"[Perplexity API] Response: {response.choices[0]}")
    return response.choices[0].message.content

def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email via SMTP using configuration details provided via environment variables.
    
    Environment Variables:
      - SMTP_HOST: SMTP server address (default: smtp.gmail.com)
      - SMTP_PORT: SMTP server port (default: 587)
      - SMTP_USER: SMTP username/email (default: your-email@gmail.com)
      - SMTP_PASSWORD: SMTP password (App Password for Gmail)
    """
    # Load SMTP configuration from environment variables.
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "your-email@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD", "your-app-password")

    # Create the email message.
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to the SMTP server, start TLS, login, and send the email.
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())
        server.quit()
        print(f"[Email] Sent email to {to} with subject '{subject}'.")
        return "Email sent."
    except Exception as e:
        print(f"[Email] Error sending email: {e}")
        return f"Failed to send email: {e}"


def video_analysis(video_url: str) -> str:
    print(
        "[Video Analysis Simulation] Steps: Download video, extract frames, analyze frames, summarize results."
    )
    return "Video analysis simulated."
