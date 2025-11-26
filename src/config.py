"""
Configuration management for MCP server
"""
import json
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class ServerConfig:
    """Server configuration"""
    name: str = "code-embedding-ai"
    version: str = "1.0.0"
    description: str = "MCP server for AI-powered code search"


@dataclass
class APIConfig:
    """FastAPI backend configuration"""
    base_url: str = "http://localhost:8000"
    timeout: int = 30


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "json"


@dataclass
class MCPConfig:
    """Main MCP configuration"""
    server: ServerConfig
    api: APIConfig
    logging: LoggingConfig

    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> "MCPConfig":
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "mcp_config.json"

        if not os.path.exists(config_path):
            # Return default configuration
            return cls(
                server=ServerConfig(),
                api=APIConfig(),
                logging=LoggingConfig()
            )

        with open(config_path, 'r') as f:
            data = json.load(f)

        return cls(
            server=ServerConfig(**data.get('server', {})),
            api=APIConfig(**data.get('api', {})),
            logging=LoggingConfig(**data.get('logging', {}))
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "server": {
                "name": self.server.name,
                "version": self.server.version,
                "description": self.server.description
            },
            "api": {
                "base_url": self.api.base_url,
                "timeout": self.api.timeout
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format
            }
        }
