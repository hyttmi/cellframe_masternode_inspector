import logging, os
from logging.handlers import RotatingFileHandler
from config import Config

log_file = os.path.join(os.path.dirname(__file__), "mncommander.log")

handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(funcName)s] [%(filename)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

logger = logging.getLogger("mncommander")
logger.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)
logger.addHandler(handler)
