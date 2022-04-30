from .utils import get_logger


log = get_logger(__name__)


class Parser(object):
    @staticmethod
    def test():
        log.info('parser -> test!')
