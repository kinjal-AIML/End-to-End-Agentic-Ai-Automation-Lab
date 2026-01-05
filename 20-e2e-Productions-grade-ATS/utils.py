import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_via_mailhog(to_email: str, subject: str, html_body: str):
    """
    Sends an HTML email to MailHog (Localhost:1025).
    """
    smtp_host = "localhost"
    smtp_port = 1025
    sender_email = "ats-system@company.com"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    # Attach HTML Body
    # We combine Body + Signature for the full email
    full_html = f"""
    <html>
      <body>
        {html_body}
      </body>
    </html>
    """
    part = MIMEText(full_html, "html")
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.sendmail(sender_email, to_email, msg.as_string())
        print(f"📧 Sent to MailHog: {to_email}")
        return True
    except Exception as e:
        print(f"❌ MailHog Error: {e}")
        return False