from loguru import logger


def demo_util():
    logger.debug("Template rooms package - Demo utility function executed successfully!")
    return {"utility": "helper", "status": "ready"}
