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
                log.info(f'child: {child} has text: {child.text}')
                for nested_child in child:
                    n_m = f'nested_child: {nested_child} with ' \
                          f'tag: {nested_child.tag}, ' \
                          f'attrib: {nested_child.attrib}, ' \
                          f'text: {nested_child.text}'
                    log.info(n_m)
                    for double_nested_child in nested_child:
                        d_m = f'double_nested_child: {double_nested_child} ' \
                              f'with tag: {double_nested_child.tag}, ' \
                              f'attrib: {double_nested_child.attrib}, ' \
                              f'text: {double_nested_child.text}'
                        log.info(d_m)
