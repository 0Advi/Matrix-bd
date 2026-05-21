"""Application configuration."""
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Z-Matrix BD Platform"
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    # TODO(auth): add JWT secret, algorithm etc when auth is wired
    debug: bool = True


settings = Settings()
