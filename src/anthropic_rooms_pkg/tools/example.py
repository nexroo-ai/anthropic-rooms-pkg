from loguru import logger


def demo_tool():
    logger.debug("Template rooms package - Demo tool executed successfully!")
    return {"tool": "template_tool", "result": "success"}