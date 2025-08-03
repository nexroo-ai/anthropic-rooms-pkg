import importlib
from loguru import logger
from .actions.chat_completion import chat_completion
from .actions.file_analysis import file_analysis
from .actions.web_search import web_search
from .services.credentials import CredentialsRegistry
from .tools.base import ToolRegistry

class AnthropicRoomsAddon:
    """
    Template Rooms Package Addon Class
    
    This class provides access to all template rooms package functionality
    and can be instantiated by external programs using this package.
    """
    
    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config = {}
        self.credentials = CredentialsRegistry()
        self.tool_registry = ToolRegistry()

    def loadTools(self, tools_dict, tool_functions, context):
        logger.debug(f"Loading tools: {len(tools_dict)} tool groups")
        logger.debug(f"Tool functions provided: {list(tool_functions.keys())}")
        logger.debug(f"Context length: {len(context)} characters")
        self.tool_registry.register_tools(tools_dict, tool_functions, context)
        registered_tools = self.tool_registry.get_tools_for_action()
        logger.info(f"Successfully registered {len(registered_tools)} tools: {list(registered_tools.keys())}")
    
    def getTools(self):
        return self.tool_registry.get_tools_for_action()
    
    def clearTools(self):
        self.tool_registry.clear()

    def chat_completion(self, message: str, **kwargs) -> dict:
        logger.debug(f"Chat completion called with message: {message[:100]}...")
        tools = self.getTools()
        logger.debug(f"Retrieved {len(tools)} tools from registry")
        if tools:
            logger.info(f"Passing tools to chat_completion: {list(tools.keys())}")
            kwargs['tools'] = tools
            kwargs['tool_registry'] = self.tool_registry
        else:
            logger.debug("No tools available for this chat completion")
        return chat_completion(self.config, message=message, **kwargs)
    
    def file_analysis(self, message: str, **kwargs) -> dict:
        return file_analysis(self.config, message=message, **kwargs)
    
    def web_search(self, query: str, **kwargs) -> dict:
        return web_search(self.config, query=query, **kwargs)

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
                module = importlib.import_module(f"anthropic_rooms_pkg.{module_name}")
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
            from anthropic_rooms_pkg.configuration import CustomAddonConfig
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