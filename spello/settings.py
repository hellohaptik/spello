import sys
import logging
import contextlib

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(level=logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@contextlib.contextmanager
def loglevel(level):
    levels = [handler.level for handler in logger.handlers]
    for handler in logger.handlers:
        handler.setLevel(level)
    yield
    for handler, olevel in zip(logger.handlers, levels):
        handler.setLevel(olevel)