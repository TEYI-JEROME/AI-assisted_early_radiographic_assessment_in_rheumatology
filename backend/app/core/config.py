from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=("settings_",),
    )

    env: str = "development"

    database_url: str = "sqlite:///./data/rheumaassist.db"

    secret_key: str = "change_me"
    jwt_issuer: str = "rheumaassist-local"
    access_token_ttl_minutes: int = 480

    cookie_name: str = "ra_access"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    csrf_cookie_name: str = "ra_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    frontend_origin: str = "http://localhost:3000"

    max_upload_mb: int = 10
    allowed_image_types: str = "image/png,image/jpeg,image/bmp"

    model_artifacts_dir: str = "../model_artifacts"
    uploads_dir: str = "../uploads"

    model_checkpoint_filename: str = "ero_resnet18_checkpoint.pth"
    model_config_filename: str = "ero_resnet18_config.json"
    model_scripted_filename: str = "ero_resnet18_scripted.pt"
    use_torchscript: bool = False

    def resolve_path(self, p: str) -> Path:
        base = Path(__file__).resolve().parents[2]
        return (base / p).resolve()


settings = Settings()