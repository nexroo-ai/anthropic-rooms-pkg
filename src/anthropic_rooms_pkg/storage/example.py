from loguru import logger


def demo_storage():
    logger.debug("Template rooms package - Demo storage started successfully!")
    return {"service": "running", "port": 8080}