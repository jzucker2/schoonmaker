#!/usr/bin/env python3
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.cli_arg_parser import CLIArgParser
from schoonmaker.parser import Parser
from schoonmaker.element_tag import ElementTag


set_up_logging()
log = get_logger(__name__)


def run():
    cli_args = CLIArgParser.get_cli_args()
    log.info(f'cli_args: {cli_args}')
    parser = Parser()
    parser.test()
    file_name = cli_args.file
    log.info(f'going with file_name: {file_name}')
    tree = parser.parse(file_name)
    log.info(f'got tree: {tree}')
    root = tree.getroot()
    r_m = f'got root: {root} with tag: {root.tag}, attrib: {root.attrib}'
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


def main():
    log.info('Begin `main` function')
    run()
    log.info('end of `main` function')


if __name__ == '__main__':
    main()
