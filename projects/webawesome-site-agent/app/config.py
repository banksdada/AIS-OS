import os
from dataclasses import dataclass
from pathlib import Path

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.environ.get(name, default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


class _DotEnv:
    """Load a .env file without overriding real environment variables."""

    @staticmethod
    def load(path: str = ".env") -> None:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class Settings:
    tidycal_token: str
    booking_type_id: str
    allowed_origins: tuple[str, ...]
    openai_api_key: str
    openai_model: str
    notify_email: str
    from_email: str
    resend_api_key: str
    crm_webhook_url: str
    user_agent: str
    site_base: str
    data_dir: str


def _dotenv_paths() -> tuple[Path, ...]:
    here = Path.cwd() / ".env"
    repo = Path(__file__).resolve().parents[3] / ".env"
    return (here,) if here == repo else (here, repo)


def load_settings(dotenv: bool = True) -> Settings:
    if dotenv:
        for path in _dotenv_paths():
            _DotEnv.load(str(path))
    return Settings(
        tidycal_token=os.environ.get("TIDYCAL_API_TOKEN", ""),
        booking_type_id=os.environ.get("TIDYCAL_BOOKING_TYPE_ID", "1292586"),
        allowed_origins=_csv(
            "ALLOWED_ORIGINS",
            "https://www.webawesome.co.uk,https://webawesome.co.uk,https://agent.webawesome.co.uk",
        ),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        notify_email=os.environ.get("NOTIFY_EMAIL", "bankoledada@gmail.com"),
        from_email=os.environ.get("FROM_EMAIL", "agent@webawesome.co.uk"),
        resend_api_key=os.environ.get("RESEND_API_KEY", ""),
        crm_webhook_url=os.environ.get("CRM_WEBHOOK_URL", ""),
        user_agent=os.environ.get("HTTP_USER_AGENT", BROWSER_UA),
        site_base=os.environ.get("SITE_BASE", "https://www.webawesome.co.uk"),
        data_dir=os.environ.get("DATA_DIR", "data"),
    )
