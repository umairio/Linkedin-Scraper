import sys

from loguru import logger as loguru_logger


def get_logger(name: str = "job_scraper"):
    """
    :param name: The name of the logger.
    :return: The logger instance.
    """
    loguru_logger.remove()

    loguru_logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            # "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "<cyan>{file.name}:{line}</cyan> - "
            "<level>{message}</level>",
        colorize=True,
    )
    loguru_logger.add(
        f"{name}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            # "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
            "{file.name}:{line} - "
            "{message}",
        colorize=True,
    )
    return loguru_logger


logger = get_logger()
