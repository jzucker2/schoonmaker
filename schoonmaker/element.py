from .utils import get_logger
from .element_tag import ElementTag


log = get_logger(__name__)


# TODO: consider renaming because XML calls it `Element` too
class Element(object):
    def __init__(self, xml_element):
        self.xml_element = xml_element

    @property
    def tag(self):
        return self.xml_element.tag

    @property
    def tag_enum(self):
        return ElementTag(self.tag)

    @property
    def is_content(self):
        return bool(self.tag_enum == ElementTag.CONTENT)

    @property
    def attrib(self):
        return self.xml_element.attrib

    @property
    def text(self):
        return self.xml_element.text

    def __repr__(self):
        return f'Element => ' \
               f'xml_element: {self.xml_element}, ' \
               f'tag: {self.tag}, ' \
               f'attrib: {self.attrib}'

    @staticmethod
    def test():
        log.info('element -> test!')
