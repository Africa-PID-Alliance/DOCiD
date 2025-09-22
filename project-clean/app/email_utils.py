from flask import current_app
from flask_mailman import EmailMessage
from . import mail

def send_email(to, subject, body):
    """
    Sends an email with the provided body content.

    Args:
        to (str): Recipient's email address.
        subject (str): Subject of the email.
        body (str): HTML content of the email.
    """
    email = EmailMessage(
        subject=subject,
        body=body,
        to=[to]
    )
    try:
        email.content_subtype = "html"  # Specify HTML content
        email.send()  # Directly send without extra app_context()
        current_app.logger.debug("SMTP email sent successfully.")
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
