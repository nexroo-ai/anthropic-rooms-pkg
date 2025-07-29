from loguru import logger


def demo_memory():
    logger.debug("Template rooms package - Demo memory system initialized successfully!")
    return {"memory_status": "active", "entries": 0}