"""
Phoenix Protocol - Configuration Management
"""
import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


# Find project root (where .env file is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Context Router settings loaded from environment variables."""
    
    # Router
    router_host: str = Field(default="127.0.0.1", env="ROUTER_HOST")
    router_port: int = Field(default=8787, env="ROUTER_PORT")
    
    # Neo4j
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")
    
    # Wallet Store
    wallet_store_path: str = Field(default="./wallet/data/wallet.db", env="WALLET_STORE_PATH")
    wallet_encryption_key: str = Field(..., env="WALLET_ENCRYPTION_KEY")
    wallet_default_persona: str = Field(default="Personal", env="WALLET_DEFAULT_PERSONA")
    
    # LLM Providers (Server-Side API Keys - NOT from user .env)
    # These are read from server environment variables, not user config
    openai_api_key: str | None = Field(
        default=None, 
        env="PHOENIX_OPENAI_API_KEY"  # Server-side key, not user key
    )
    openai_model: str = Field(default="gpt-4o-mini", env="PHOENIX_OPENAI_MODEL")
    anthropic_api_key: str | None = Field(
        default=None,
        env="PHOENIX_ANTHROPIC_API_KEY"  # Server-side key, not user key
    )
    anthropic_model: str = Field(default="claude-3-haiku-20240307", env="PHOENIX_ANTHROPIC_MODEL")
    
    # Local LLM (fallback)
    ollama_model: str = Field(default="llama3.2", env="OLLAMA_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # LLM Provider preference
    llm_provider_preference: str = Field(default="openai", env="LLM_PROVIDER_PREFERENCE")  # openai, anthropic, ollama
    
    # MemMachine
    memmachine_api_key: str | None = Field(default=None, env="MEMMACHINE_API_KEY")
    memmachine_base_url: str = Field(default="http://localhost:8080", env="MEMMACHINE_BASE_URL")
    memmachine_enabled: bool = Field(default=True, env="MEMMACHINE_ENABLED")
    
    def get_wallet_path(self) -> Path:
        """Get absolute path to wallet database."""
        wallet_path = Path(self.wallet_store_path)
        if wallet_path.is_absolute():
            return wallet_path
        return PROJECT_ROOT / wallet_path
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    
    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields in .env (like memverge settings)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

