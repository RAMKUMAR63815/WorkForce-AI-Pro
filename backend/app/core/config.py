
from functools import lru_cache #Saves the settings so they don't need to be loaded repeatedly

from pydantic_settings import BaseSettings, SettingsConfigDict #Configures how settings are loaded
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "WorkForce AI Pro"

    # Inside Docker, use the Compose service name: mysql
    db_host: str = "mysql"
    db_port: int = 3306
    db_name: str = "workforce_db"
    db_user: str = "workforce_user"
    db_password: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    password_reset_debug: bool = False

    @property#Function-ai variable maadhiri use panradhu.
    def database_url(self) -> URL:
        """Build a database URL safely, including special characters."""
        return URL.create(
            drivername="mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache(maxsize=1) #First time create pannina result-ah save panni reuse panradhu.
def get_settings() -> Settings:
    """Load settings once and reuse them throughout the application."""
    return Settings()
