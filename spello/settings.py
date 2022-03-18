import contextlib
import logging
import sys

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setLevel(level=logging.DEBUG)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


@contextlib.contextmanager
def loglevel(level):
    levels = [handler.level for handler in logger.handlers]
    for handler in logger.handlers:
        handler.setLevel(level)
    yield
    for handler, olevel in zip(logger.handlers, levels):
        handler.setLevel(olevel)
