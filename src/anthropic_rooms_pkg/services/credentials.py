from typing import Dict, Optional
from loguru import logger


class CredentialsRegistry:
    _instance: Optional['CredentialsRegistry'] = None
    _credentials: Dict[str, str] = {}
    
    def __new__(cls) -> 'CredentialsRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def store(self, key: str, value: str) -> None:
        self._credentials[key] = value
        logger.debug(f"Stored credential: {key}")
    
    def store_multiple(self, credentials: Dict[str, str]) -> None:
        for key, value in credentials.items():
            self.store(key, value)
    
    def get(self, key: str) -> Optional[str]:
        return self._credentials.get(key)
    
    def has(self, key: str) -> bool:
        return key in self._credentials
    
    def clear(self) -> None:
        self._credentials.clear()
        logger.debug("Cleared all credentials")
    
    def keys(self) -> list:
        return list(self._credentials.keys())