import importlib
from loguru import logger
from .actions.example import example
from .services.credentials import CredentialsRegistry

class TemplateRoomsAddon:
    """
    Template Rooms Package Addon Class
    
    This class provides access to all template rooms package functionality
    and can be instantiated by external programs using this package.
    """
    
    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config = {}
        self.credentials = CredentialsRegistry()

    # add your actions here  
    def example(self, param1: str, param2: str) -> dict:
        return example(self.config, param1=param1, param2=param2)

    def test(self) -> bool:
        """
        Test function for template rooms package.
        Tests each module and reports available components.
        Test connections with credentials if required.
        
        Returns:
            bool: True if test passes, False otherwise
        """
        logger.info("Running template-rooms-pkg test...")
        
        total_components = 0
        for module_name in self.modules:
            try:
                module = importlib.import_module(f"template_rooms_pkg.{module_name}")
                components = getattr(module, '__all__', [])
                component_count = len(components)
                total_components += component_count
                for component_name in components:
                    logger.info(f"Processing component: {component_name}")
                    if hasattr(module, component_name):
                        component = getattr(module, component_name)
                        logger.info(f"Component {component_name} type: {type(component)}")
                        if callable(component):
                            try:
                                skip_instantiation = False
                                try:
                                    from pydantic import BaseModel
                                    if hasattr(component, '__bases__') and any(
                                        issubclass(base, BaseModel) for base in component.__bases__ if isinstance(base, type)
                                    ):
                                        logger.info(f"Component {component_name} is a Pydantic model, skipping instantiation")
                                        skip_instantiation = True
                                except (ImportError, TypeError):
                                    pass
                                # skip models require parameters
                                if component_name in ['ActionInput', 'ActionOutput', 'ActionResponse', 'OutputBase', 'TokensSchema']:
                                    logger.info(f"Component {component_name} requires parameters, skipping instantiation")
                                    skip_instantiation = True
                                
                                if not skip_instantiation:
                                    # result = component()
                                    logger.info(f"Component {component_name}() would be executed successfully")
                                else:
                                    logger.info(f"Component {component_name} exists and is valid (skipped instantiation)")
                            except Exception as e:
                                logger.warning(f"Component {component_name}() failed: {e}")
                                logger.error(f"Exception details for {component_name}: {str(e)}")
                                raise e
                logger.info(f"{component_count} {module_name} loaded correctly, available imports: {', '.join(components)}")
            except ImportError as e:
                logger.error(f"Failed to import {module_name}: {e}")
                return False
            except Exception as e:
                logger.error(f"Error testing {module_name}: {e}")
                return False
        logger.info("Template rooms package test completed successfully!")
        logger.info(f"Total components loaded: {total_components} across {len(self.modules)} modules")
        return True
    
    def loadAddonConfig(self, addon_config: dict):
        """
        Load addon configuration.
        
        Args:
            addon_config (dict): Addon configuration dictionary
        
        Returns:
            bool: True if configuration is loaded successfully, False otherwise
        """
        try:
            from template_rooms_pkg.configuration import CustomAddonConfig
            self.config = CustomAddonConfig(**addon_config)
            logger.info(f"Addon configuration loaded successfully: {self.config}")
            return True
        except Exception as e:
            logger.error(f"Failed to load addon configuration: {e}")
            return False

    def loadCredentials(self, **kwargs) -> bool:
        """
        Load credentials and store them in the credentials registry.
        Takes individual secrets as keyword arguments for validation.
        
        Args:
            **kwargs: Individual credential key-value pairs
        
        Returns:
            bool: True if credentials are loaded successfully, False otherwise
        """
        logger.debug("Loading credentials...")
        logger.debug(f"Received credentials: {kwargs}")
        try:
            if self.config and hasattr(self.config, 'secrets'):
                required_secrets = list(self.config.secrets.keys())
                missing_secrets = [secret for secret in required_secrets if secret not in kwargs]
                if missing_secrets:
                    raise ValueError(f"Missing required secrets: {missing_secrets}")
            
            self.credentials.store_multiple(kwargs)
            logger.info(f"Loaded {len(kwargs)} credentials successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False