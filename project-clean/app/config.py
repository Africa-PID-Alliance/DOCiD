# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SMTP Server Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (
        os.getenv('MAIL_DEFAULT_SENDER_NAME', 'AFRICA PID Alliance'),
        os.getenv('MAIL_DEFAULT_SENDER_EMAIL', 'info@africapidalliance.org')
    )
    MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', '5'))

    # Debugging Configuration
    MAIL_DEBUG = os.getenv('MAIL_DEBUG', 'False').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
