import pytest
from pydantic import ValidationError

from anthropic_rooms_pkg.configuration.addonconfig import CustomAddonConfig
from anthropic_rooms_pkg.configuration.baseconfig import BaseAddonConfig


class TestBaseAddonConfig:
    def test_base_config_creation(self):
        config = BaseAddonConfig(
            id="test_addon_id",
            type="test_type",
            name="test_addon",
            description="Test addon description",
            secrets={"key1": "value1"}
        )

        assert config.id == "test_addon_id"
        assert config.type == "test_type"
        assert config.name == "test_addon"
        assert config.description == "Test addon description"
        assert config.secrets == {"key1": "value1"}
        assert config.enabled is True

    def test_base_config_defaults(self):
        config = BaseAddonConfig(
            id="test_id",
            type="test_type",
            name="test",
            description="Test description"
        )

        assert config.enabled is True
        assert config.secrets == {}
        assert config.config == {}


class TestCustomAddonConfig:
    def test_custom_config_creation_success(self):
        config = CustomAddonConfig(
            id="test_anthropic_addon_id",
            name="test_anthropic_addon",
            description="Test Anthropic addon",
            type="agent",
            secrets={"anthropic_api_key": "test_key"}
        )

        assert config.id == "test_anthropic_addon_id"
        assert config.name == "test_anthropic_addon"
        assert config.type == "agent"
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_custom_config_with_custom_values(self):
        config = CustomAddonConfig(
            id="test_anthropic_addon_id",
            name="test_anthropic_addon",
            description="Test Anthropic addon",
            type="agent",
            model="claude-3-opus",
            max_tokens=8192,
            temperature=0.5,
            secrets={"anthropic_api_key": "test_key"}
        )

        assert config.model == "claude-3-opus"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5

    def test_custom_config_missing_anthropic_api_key(self):
        with pytest.raises(ValidationError, match="Missing Anthropic secrets"):
            CustomAddonConfig(
                id="test_anthropic_addon_id",
                name="test_anthropic_addon",
                description="Test Anthropic addon",
                type="agent",
                secrets={}
            )

    def test_custom_config_missing_required_fields(self):
        with pytest.raises(ValidationError):
            CustomAddonConfig(
                id="test_anthropic_addon_id",
                name="test_anthropic_addon",
                description="Test Anthropic addon",
                secrets={"anthropic_api_key": "test_key"}
            )
