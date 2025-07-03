# src/utils/config_loader.py
import yaml
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Utility class for loading configuration files.

    This class implements the Singleton pattern to ensure only one instance
    of the configuration is loaded and used throughout the application.
    """
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only load config if it hasn't been loaded
        if self._config is None:
            self._config = self._load_guild_config()

    def _load_guild_config(self) -> dict:
        """Load the guild configuration file.

        Returns:
            dict: The loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        config_path = ""
        try:
            config_path = Path(__file__).parents[1] / 'config' / 'guild_config.yaml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info("Guild configuration loaded successfully")
                return config
        except FileNotFoundError:
            logger.error(f"Config file not found at {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            raise

    @property
    def config(self) -> dict:
        """Get the loaded configuration.

        Returns:
            dict: The loaded configuration
        """
        return self._config

    def get_channel_name(self, channel_key: str) -> Optional[str]:
        """Get channel name from config.

        Args:
            channel_key (str): Key of the channel in config

        Returns:
            Optional[str]: Channel name if found, None otherwise
        """
        try:
            return self.config['channels'][channel_key]['name']
        except KeyError:
            logger.error(f"Channel key '{channel_key}' not found in config")
            return None

    def get_role_name(self, role_key: str) -> Optional[str]:
        """Get role name from config.

        Args:
            role_key (str): Key of the role in config

        Returns:
            Optional[str]: Role name if found, None otherwise
        """
        try:
            return self.config['roles'][role_key]['name']
        except KeyError:
            logger.error(f"Role key '{role_key}' not found in config")
            return None

    def get_role_id(self, role_name: str) -> Optional[str]:
        """Get role id from config.

        Args:
            role_name (str): name of the role in config

        Returns:
            Optional[str]: Role name if found, None otherwise
        """

        for key, attributes in self.config['roles'].items():
            if attributes.get('name') == role_name:
                return key

        logger.error(f"Role name '{role_name}' not found in config")
        return None
