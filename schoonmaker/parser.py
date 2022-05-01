import xml.etree.ElementTree as ET
from .utils import get_logger
from .element_tag import ElementTag


log = get_logger(__name__)


class Parser(object):
    @staticmethod
    def test():
        log.info('parser -> test!')

    @classmethod
    def parse(cls, file_name):
        return ET.parse(file_name)

    def parse_content(self, element):
        log.info('!!!!!! we are parsing content!!!')
        log.info(f'Content element: {element} has text: {element.text}')
        for nested_element in element:
            n_m = f'nested_element: {nested_element} with ' \
                  f'tag: {nested_element.tag}, ' \
                  f'attrib: {nested_element.attrib}, ' \
                  f'text: {nested_element.text}'
            log.info(n_m)
            for double_nested_element in nested_element:
                d_m = f'double_nested_element: {double_nested_element} ' \
                      f'with tag: {double_nested_element.tag}, ' \
                      f'attrib: {double_nested_element.attrib}, ' \
                      f'text: {double_nested_element.text}'
                log.info(d_m)

    def naive_parse(self, file_name):
        log.info(f'going with file_name: {file_name}')
        tree = self.parse(file_name)
        log.info(f'got tree: {tree}')
        root = tree.getroot()
        r_m = f'got root: {root} with ' \
              f'tag: {root.tag}, ' \
              f'attrib: {root.attrib}'
        log.info(r_m)
        for child in root:
            c_m = f'child: {child} with ' \
                  f'tag: {child.tag}, ' \
                  f'attrib: {child.attrib}'
            log.info(c_m)
            if child.tag == ElementTag.CONTENT.value:
                log.info('we found content!!!')
                log.info(f'Content child: {child} has text: {child.text}')
                self.parse_content(child)
