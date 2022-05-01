import xml.etree.ElementTree as ET
from .utils import get_logger


log = get_logger(__name__)


class Parser(object):
    @staticmethod
    def test():
        log.info('parser -> test!')

    @classmethod
    def parse(cls, file_name):
        return ET.parse(file_name)
