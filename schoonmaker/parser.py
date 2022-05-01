import xml.etree.ElementTree as ET
from .utils import get_logger
from .element_tag import ElementTag
from .element import Element


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
        el = Element(element)
        log.info(f'el: {el}')
        for nested_element in element:
            n_m = f'nested_element: {nested_element} with ' \
                  f'tag: {nested_element.tag}, ' \
                  f'attrib: {nested_element.attrib}, ' \
                  f'text: {nested_element.text}'
            log.info(n_m)
            nested_el = Element(nested_element)
            log.info(f'nested_el: {nested_el}')
            for double_nested_element in nested_element:
                d_m = f'double_nested_element: {double_nested_element} ' \
                      f'with tag: {double_nested_element.tag}, ' \
                      f'attrib: {double_nested_element.attrib}, ' \
                      f'text: {double_nested_element.text}'
                log.info(d_m)
                double_nested_el = Element(double_nested_element)
                log.info(f'double_nested_el: {double_nested_el}')

    def naive_parse(self, file_name):
        log.info(f'going with file_name: {file_name}')
        tree = self.parse(file_name)
        log.info(f'got tree: {tree}')
        root = tree.getroot()
        r_m = f'got root: {root} with ' \
              f'tag: {root.tag}, ' \
              f'attrib: {root.attrib}'
        log.info(r_m)
        root_element = Element(root)
        log.info(f'root_element: {root_element}')
        for child in root:
            c_m = f'child: {child} with ' \
                  f'tag: {child.tag}, ' \
                  f'attrib: {child.attrib}'
            log.info(c_m)
            child_element = Element(child)
            log.info(f'child_element: {child_element}')
            if child.tag == ElementTag.CONTENT.value:
                log.info('we found content!!!')
                log.info(f'Content child: {child} has text: {child.text}')
                self.parse_content(child)
