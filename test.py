#!/usr/bin/env python3
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.parser import Parser
from schoonmaker.element_tag import ElementTag


set_up_logging()
log = get_logger(__name__)


def run():
    parser = Parser()
    parser.test()
    file_name = 'samples/final_draft_sample.fdx'
    log.info(f'hardcoded file_name: {file_name}')
    parser.naive_parse(file_name)
    log.info('done with `run`')


def main():
    log.info('Begin `main` function')
    run()
    log.info('end of `main` function')


if __name__ == '__main__':
    main()
