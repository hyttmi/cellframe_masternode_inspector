import logging, os
from logging.handlers import RotatingFileHandler
from config import Config

import collections

class RingBufferHandler(logging.Handler):
    def __init__(self, maxlen=5000):
        super().__init__()
        self.ring_buffer = collections.deque(maxlen=maxlen)

    def emit(self, record):
        self.ring_buffer.append(self.format(record))

    def get_logs(self):
        return list(self.ring_buffer)

log_file = os.path.join(os.path.dirname(__file__), "mninspector.log")

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,
    backupCount=5
)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] [%(funcName)s] [%(filename)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG if Config.DEBUG else logging.INFO)

ring_handler = RingBufferHandler(maxlen=5000)
ring_handler.setFormatter(formatter)
ring_handler.setLevel(logging.DEBUG)

logger = logging.getLogger("mninspector")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(ring_handler)
