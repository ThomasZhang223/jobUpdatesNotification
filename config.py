from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API key for protected endpoints
    api_key: str

    # Brevo settings
    brevo_api_key: str
    mail_from: str
    
    # JsonBin key
    jsonbin_api_key: str
    
    # Repository URLs
    canadian_internships_url: str = "https://github.com/negarprh/Canadian-Tech-Internships-2026"
    us_internships_url: str = "https://github.com/SimplifyJobs/Summer2026-Internships/tree/dev"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
