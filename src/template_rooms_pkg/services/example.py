from loguru import logger


def demo_service():
    logger.debug("Template rooms package - Demo service started successfully!")
    return {"service": "running", "port": 8080}