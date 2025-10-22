import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    CROSSREF_API_URL = os.getenv('CROSSREF_API_URL')
    CROSSREF_API_KEY = os.getenv('CROSSREF_API_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    LC_API_KEY = os.getenv('LC_API_KEY')
    LOCAL_CONTEXTS_API_BASE_URL = os.getenv('LOCAL_CONTEXTS_API_BASE_URL')
    CSTR_CLIENT_ID = os.getenv('CSTR_CLIENT_ID')
    CSTR_SECRET = os.getenv('CSTR_SECRET')
    CSTR_PREFIX = os.getenv('CSTR_PREFIX')
    CSTR_USERNAME = os.getenv('CSTR_USERNAME')
    APPLICATION_BASE_URL = os.getenv('APPLICATION_BASE_URL', 'http://localhost:5000')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

    # CORDRA Configuration
    CORDRA_BASE_URL = os.getenv('CORDRA_BASE_URL', 'https://cordra.kenet.or.ke/cordra')
    CORDRA_USERNAME = os.getenv('CORDRA_USERNAME')
    CORDRA_PASSWORD = os.getenv('CORDRA_PASSWORD')

    # RAID Configuration
    RAID_API_URL = os.getenv('RAID_API_URL', 'https://api.demo.raid.org.au/raid/')
    RAID_TOKEN_URL = os.getenv('RAID_TOKEN_URL', 'https://iam.demo.raid.org.au/realms/raid/protocol/openid-connect/token')
    RAID_GRANT_TYPE = os.getenv('RAID_GRANT_TYPE', 'password')
    RAID_CLIENT_ID = os.getenv('RAID_CLIENT_ID')
    RAID_CLIENT_SECRET = os.getenv('RAID_CLIENT_SECRET')
    RAID_USERNAME = os.getenv('RAID_USERNAME')
    RAID_PASSWORD = os.getenv('RAID_PASSWORD')

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours in seconds (default)
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days in seconds (default)
 