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
    type = "agent"
    
    def __init__(self):
        self.modules = ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        self.config = {}
        self.credentials = CredentialsRegistry()
        self.tool_registry = ToolRegistry()
        self.observer_callback = None
        self.addon_id = None
    
    @property
    def logger(self):
        """Custom logger that prefixes all messages with addon type"""
        class PrefixedLogger:
            def __init__(self, addon_type):
                self.addon_type = addon_type
                self._logger = logger
            
            def debug(self, message):
                self._logger.debug(f"[TYPE: {self.addon_type.upper()}] {message}")
            
            def info(self, message):
                self._logger.info(f"[TYPE: {self.addon_type.upper()}] {message}")
            
            def warning(self, message):
                self._logger.warning(f"[TYPE: {self.addon_type.upper()}] {message}")
            
            def error(self, message):
                self._logger.error(f"[TYPE: {self.addon_type.upper()}] {message}")
        
        return PrefixedLogger(self.type)

    def loadTools(self, tool_functions, tool_descriptions=None, tool_max_retries=None):
        self.logger.debug(f"Tool functions provided: {list(tool_functions.keys())}")
        self.logger.debug(f"Tool descriptions provided: {tool_descriptions}")
        self.logger.debug(f"Tool max retries provided: {tool_max_retries}")
        self.tool_registry.register_tools(tool_functions, tool_descriptions, tool_max_retries)
        registered_tools = self.tool_registry.get_tools_for_action()
        self.logger.info(f"Successfully registered {len(registered_tools)} tools: {list(registered_tools.keys())}")
    
    def getTools(self):
        return self.tool_registry.get_tools_for_action()
    
    def clearTools(self):
        self.tool_registry.clear()

    def setObserverCallback(self, callback, addon_id: str):
        self.observer_callback = callback
        self.addon_id = addon_id

    def chat_completion(self, message: str, **kwargs) -> dict:
        self.logger.debug(f"Chat completion called with message: {message[:100]}...")
        tools = self.getTools()
        self.logger.debug(f"Retrieved {len(tools)} tools from registry")
        if tools:
            self.logger.info(f"Passing tools to chat_completion: {list(tools.keys())}")
            kwargs['tools'] = tools
            kwargs['tool_registry'] = self.tool_registry
        else:
            self.logger.debug("No tools available for this chat completion")
        
        if self.observer_callback and self.addon_id:
            kwargs['observer_callback'] = self.observer_callback
            kwargs['addon_id'] = self.addon_id
            
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
        self.logger.info("Running template-rooms-pkg test...")
        
        total_components = 0
        for module_name in self.modules:
            try:
                module = importlib.import_module(f"anthropic_rooms_pkg.{module_name}")
                components = getattr(module, '__all__', [])
                component_count = len(components)
                total_components += component_count
                for component_name in components:
                    self.logger.info(f"Processing component: {component_name}")
                    if hasattr(module, component_name):
                        component = getattr(module, component_name)
                        self.logger.info(f"Component {component_name} type: {type(component)}")
                        if callable(component):
                            try:
                                skip_instantiation = False
                                try:
                                    from pydantic import BaseModel
                                    if hasattr(component, '__bases__') and any(
                                        issubclass(base, BaseModel) for base in component.__bases__ if isinstance(base, type)
                                    ):
                                        self.logger.info(f"Component {component_name} is a Pydantic model, skipping instantiation")
                                        skip_instantiation = True
                                except (ImportError, TypeError):
                                    pass
                                # skip models require parameters
                                if component_name in ['ActionInput', 'ActionOutput', 'ActionResponse', 'OutputBase', 'TokensSchema']:
                                    self.logger.info(f"Component {component_name} requires parameters, skipping instantiation")
                                    skip_instantiation = True
                                
                                if not skip_instantiation:
                                    # result = component()
                                    self.logger.info(f"Component {component_name}() would be executed successfully")
                                else:
                                    self.logger.info(f"Component {component_name} exists and is valid (skipped instantiation)")
                            except Exception as e:
                                self.logger.warning(f"Component {component_name}() failed: {e}")
                                self.logger.error(f"Exception details for {component_name}: {str(e)}")
                                raise e
                self.logger.info(f"{component_count} {module_name} loaded correctly, available imports: {', '.join(components)}")
            except ImportError as e:
                self.logger.error(f"Failed to import {module_name}: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Error testing {module_name}: {e}")
                return False
        self.logger.info("Template rooms package test completed successfully!")
        self.logger.info(f"Total components loaded: {total_components} across {len(self.modules)} modules")
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
            self.logger.info(f"Addon configuration loaded successfully: {self.config}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load addon configuration: {e}")
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
        self.logger.debug("Loading credentials...")
        self.logger.debug(f"Received credentials: {kwargs}")
        try:
            if self.config and hasattr(self.config, 'secrets'):
                required_secrets = list(self.config.secrets.keys())
                missing_secrets = [secret for secret in required_secrets if secret not in kwargs]
                if missing_secrets:
                    raise ValueError(f"Missing required secrets: {missing_secrets}")
            
            self.credentials.store_multiple(kwargs)
            self.logger.info(f"Loaded {len(kwargs)} credentials successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load credentials: {e}")
            return False