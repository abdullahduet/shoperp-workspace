from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    # Comma-separated list of allowed CORS origins.
    # Set ALLOWED_ORIGINS in production to your Netlify URL.
    # Example: https://your-app.netlify.app
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
