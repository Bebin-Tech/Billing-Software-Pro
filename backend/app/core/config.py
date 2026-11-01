from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str = 'mysql+pymysql://gst:gst@127.0.0.1:3306/gst_billing'
    jwt_secret: str
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173'
    registration_enabled: bool = False
    secure_cookies: bool = True
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_user: str = ''
    smtp_password: str = ''
    smtp_from: str = ''
    frontend_url: str = 'http://127.0.0.1:5173'
    require_email_verification: bool = False


settings = Settings()
if len(settings.jwt_secret) < 32:
    raise ValueError('JWT_SECRET must contain at least 32 characters')
