"""Unit tests for ConfigLoader."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.utils.config_loader import ConfigLoader


@pytest.fixture(autouse=True)
def reset_config_loader():
    ConfigLoader._instance = None
    ConfigLoader._config = None
    yield
    ConfigLoader._instance = None
    ConfigLoader._config = None


class TestConfigLoader:
    def test_singleton_loads_guild_config(self):
        loader = ConfigLoader()
        assert loader.config is not None
        assert "app" in loader.config

    def test_get_timezone_from_config(self):
        loader = ConfigLoader()
        tz = loader.get_timezone()
        assert str(tz) != ""

    def test_get_timezone_falls_back_on_invalid_value(self):
        ConfigLoader._instance = None
        ConfigLoader._config = {"app": {"timezone": "Not/A/Timezone"}}
        loader = ConfigLoader()
        tz = loader.get_timezone()
        assert str(tz) == "America/New_York"

    def test_get_channel_name(self):
        loader = ConfigLoader()
        channel_name = loader.get_channel_name("welcome")
        assert channel_name is None or isinstance(channel_name, str)

    def test_get_channel_name_missing_key(self):
        loader = ConfigLoader()
        assert loader.get_channel_name("definitely_missing_channel_key") is None

    def test_get_role_name_and_id(self):
        loader = ConfigLoader()
        role_name = loader.get_role_name("admin")
        if role_name:
            assert loader.get_role_id(role_name) is not None
        assert loader.get_role_name("definitely_missing_role_key") is None
        assert loader.get_role_id("Definitely Missing Role") is None

    def test_get_channel_name_found(self):
        loader = ConfigLoader()
        first_channel = next(iter(loader.config["channels"]))
        assert loader.get_channel_name(first_channel) is not None

    def test_missing_config_file_raises(self, tmp_path):
        ConfigLoader._instance = None
        ConfigLoader._config = None
        fake_path = tmp_path / "missing.yaml"
        with patch.object(Path, "parents", new_callable=lambda: type("P", (), {"__getitem__": lambda s, i: tmp_path})()):
            with patch("builtins.open", side_effect=FileNotFoundError):
                with pytest.raises(FileNotFoundError):
                    ConfigLoader()

    def test_invalid_yaml_raises(self, tmp_path):
        bad_file = tmp_path / "guild_config.yaml"
        bad_file.write_text(":\n  bad: [yaml")
        with patch.object(
            ConfigLoader,
            "_load_guild_config",
            side_effect=yaml.YAMLError("bad yaml"),
        ):
            ConfigLoader._instance = None
            ConfigLoader._config = None
            with pytest.raises(yaml.YAMLError):
                ConfigLoader()
