"""Configuration loader utility."""
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """Load configuration from YAML files."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
    
    def load_agents_config(self) -> Dict[str, Any]:
        """Load agents configuration."""
        with open(self.config_dir / "agents.yaml", "r") as f:
            return yaml.safe_load(f)
    
    def load_database_config(self) -> Dict[str, Any]:
        """Load database configuration."""
        with open(self.config_dir / "database.yaml", "r") as f:
            return yaml.safe_load(f)
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        config = self.load_agents_config()
        return config.get(agent_name, {})

# Global config instance
config_loader = ConfigLoader()

