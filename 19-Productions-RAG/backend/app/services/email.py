from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import Config

# Configure Connection
conf = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_lead_alert(user_email: str, page_source: str, summary: str):
    """
    Sends an alert to the BYV Admin Team when a user gives their email.
    """
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd;">
        <h2 style="color: #7C3AED;">🚀 New Lead Captured</h2>
        <p><strong>User Email:</strong> <a href="mailto:{user_email}">{user_email}</a></p>
        <p><strong>Source Page:</strong> {page_source}</p>
        <hr>
        <h3>Context / Request:</h3>
        <p style="background-color: #f9f9f9; padding: 15px;">{summary}</p>
        <hr>
        <p style="font-size: 12px; color: #888;">Sent automatically by BYV Architect Agent.</p>
    </div>
    """

    message = MessageSchema(
        subject=f"[New Lead] Inquiry from {page_source}",
        recipients=[Config.ADMIN_EMAIL], # Send to YOU
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False