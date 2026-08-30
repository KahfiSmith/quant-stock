from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "postgresql+psycopg://quantlens:quantlens@localhost:5432/quantlens"
    frontend_origin: str = "http://localhost:3000"
    jwt_secret: str = Field(
        default="development-only-jwt-secret-must-be-replaced",
        min_length=32,
    )
    jwt_issuer: str = "quantlens-api"
    jwt_audience: str = "quantlens-web"
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_ttl_seconds: int = Field(default=60 * 60 * 24 * 30, ge=3600)
    refresh_token_hmac_key: str = Field(
        default="development-only-refresh-secret-must-be-replaced",
        min_length=32,
    )
    cookie_name: str = "quantlens_refresh"
    cookie_path: str = "/api/v1/auth"
    cookie_secure: bool = False
    cookie_same_site: Literal["lax", "strict", "none"] = "lax"
    auth_rate_limit_per_minute: int = Field(default=20, ge=1, le=1000)


    ai_analyst_provider: Literal[
        "deterministic", "mock_llm", "openai_compatible", "anthropic_compatible"
    ] = "deterministic"
    ai_analyst_api_key: str | None = None
    ai_analyst_base_url: str | None = None
    ai_analyst_model: str = "gpt-4o-mini"
    ai_analyst_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)




    market_data_provider: Literal["sample", "yfinance"] = "yfinance"
    yfinance_enabled: bool = True
    yfinance_request_timeout_seconds: float = Field(default=15.0, ge=1.0, le=60.0)
    yfinance_default_period: str = "2y"
    yfinance_symbol_suffix: str = ".JK"
    yfinance_proxy: str | None = None




    yfinance_symbols: str = (
        "BBCA,BMRI,BBRI,TLKM,ASII,UNVR,INDF,ICBP,KLBF,SMGR,"
        "BNBR,BUMI,UNSP,ELTY,ENRG,BTEL,DEWA,BRMS,VIVA,MDIA,JGLE,ALII,"
        "UNTR,PAMA,DOID,PTBA,ADRO,HRUM,GEMS,BYAN,MBAP,KKGI,"
        "BRPT,BREN,TPIA,CUAN,PTRO,GZCO,CDIA,"
        "TINS,NICK,CITA,RMKE,SMMT,ARCI,BRNA,"
        "PWON,BSDE,CTRA,SMRA,APLN,KIJA,ELSA,RAJA,GMFI,JIHD,"
        "BUKA,EMTK,DCII,TFAS,EDGE,MTDL,WEGE,TOTL,TRUE,"
        "BUVA,DSSA,IATA,KOTA,BULL,INET,PADA,SLIS,VKTR,"
        "ERAA,IMPC,GRPH,HUMI"
    )

    @model_validator(mode="after")
    def reject_default_secrets_outside_development(self) -> "Settings":
        defaults = {
            "development-only-jwt-secret-must-be-replaced",
            "development-only-refresh-secret-must-be-replaced",
        }
        if self.app_env in {"staging", "production"} and (
            self.jwt_secret in defaults or self.refresh_token_hmac_key in defaults
        ):
            raise ValueError("Development secrets cannot be used outside local development")
        return self

    @field_validator("frontend_origin")
    @classmethod
    def normalize_frontend_origin(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def yfinance_symbols_list(self) -> list[str]:
        return [s.strip().upper() for s in self.yfinance_symbols.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
