from unittest.mock import patch

import pytest

from anthropic_rooms_pkg.services.credentials import CredentialsRegistry


class TestCredentialsRegistry:
    def setup_method(self):
        CredentialsRegistry._instance = None
        CredentialsRegistry._credentials = {}

    def test_credentials_registry_singleton(self):
        registry1 = CredentialsRegistry()
        registry2 = CredentialsRegistry()

        assert registry1 is registry2
        assert CredentialsRegistry._instance is registry1

    def test_store_credential(self):
        registry = CredentialsRegistry()

        registry.store("test_key", "test_value")

        assert registry.get("test_key") == "test_value"

    def test_store_multiple_credentials(self):
        registry = CredentialsRegistry()
        credentials = {"key1": "value1", "key2": "value2"}

        with patch.object(registry, 'store') as mock_store:
            registry.store_multiple(credentials)

            assert mock_store.call_count == 2
            mock_store.assert_any_call("key1", "value1")
            mock_store.assert_any_call("key2", "value2")

    def test_get_existing_credential(self):
        registry = CredentialsRegistry()
        registry._credentials["test_key"] = "test_value"

        result = registry.get("test_key")

        assert result == "test_value"

    def test_get_nonexistent_credential(self):
        registry = CredentialsRegistry()

        result = registry.get("nonexistent_key")

        assert result is None

    def test_has_existing_credential(self):
        registry = CredentialsRegistry()
        registry._credentials["test_key"] = "test_value"

        result = registry.has("test_key")

        assert result is True

    def test_has_nonexistent_credential(self):
        registry = CredentialsRegistry()

        result = registry.has("nonexistent_key")

        assert result is False

    def test_clear_credentials(self):
        registry = CredentialsRegistry()
        registry._credentials = {"key1": "value1", "key2": "value2"}

        registry.clear()

        assert len(registry._credentials) == 0

    def test_keys(self):
        registry = CredentialsRegistry()
        registry._credentials = {"key1": "value1", "key2": "value2"}

        result = registry.keys()

        assert sorted(result) == ["key1", "key2"]
        assert isinstance(result, list)

    def test_keys_empty(self):
        registry = CredentialsRegistry()

        result = registry.keys()

        assert result == []
