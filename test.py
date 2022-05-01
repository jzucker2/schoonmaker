#!/usr/bin/env python3
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.parser import Parser


set_up_logging()
log = get_logger(__name__)


def run():
    parser = Parser()
    parser.test()
    file_name = 'samples/final_draft_sample.fdx'
    log.info(f'going with file_name: {file_name}')
    tree = parser.parse(file_name)
    log.info(f'got tree: {tree}')
    root = tree.getroot()
    log.info(f'got root: {root}')
    for child in root:
        c_m = f'child: {child} with ' \
              f'tag: {child.tag}, ' \
              f'attrib: {child.attrib}'
        log.info(c_m)


def main():
    log.info('Begin `main` function')
    run()
    log.info('end of `main` function')


if __name__ == '__main__':
    main()
