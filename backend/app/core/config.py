"""
Core configuration settings for the NER Landslide Early Warning System.
Loads environment variables using Pydantic Settings with sane defaults.
"""

from pathlib import Path
from typing import List, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project Information
    PROJECT_NAME: str = "NER Landslide Early Warning & Risk Monitoring System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_PATH: str = str(BASE_DIR / "data" / "landslide_system.db")

    # Machine Learning Service Settings
    ML_MODEL_DIR: str = str(BASE_DIR / "backend" / "ml_engine" / "models")
    SPATIAL_MODEL_FILENAME: str = "landslide_rf_model.joblib"
    METADATA_FILENAME: str = "model_metadata.json"

    # Early Warning Empirical Thresholds
    RAINFALL_YELLOW_THRESHOLD_MM: float = 40.0
    RAINFALL_ORANGE_THRESHOLD_MM: float = 75.0
    RAINFALL_RED_THRESHOLD_MM: float = 120.0
    SOIL_MOISTURE_CRITICAL_PCT: float = 80.0

    @property
    def model_file_path(self) -> Path:
        return Path(self.ML_MODEL_DIR) / self.SPATIAL_MODEL_FILENAME

    @property
    def metadata_file_path(self) -> Path:
        return Path(self.ML_MODEL_DIR) / self.METADATA_FILENAME


settings = Settings()
