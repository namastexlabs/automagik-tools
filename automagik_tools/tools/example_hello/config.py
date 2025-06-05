"""Configuration for Example Hello tool"""
from pydantic_settings import BaseSettings


class ExampleHelloConfig(BaseSettings):
    """Configuration for Example Hello tool"""
    # This is a simple example with no required configuration
    # Add your tool-specific settings here
    
    model_config = {
        "env_prefix": "EXAMPLE_HELLO_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }