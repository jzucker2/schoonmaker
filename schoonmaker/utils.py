import logging


def set_up_logging(level=logging.DEBUG):
    format = "[%(levelname)s] %(asctime)s %(message)s"
    logging.basicConfig(format=format, level=level)


# pass in __name__
def get_logger(name):
    return logging.getLogger(name)
