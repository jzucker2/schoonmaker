#!/usr/bin/env python3
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.parser import Parser


set_up_logging()
log = get_logger(__name__)


def run():
    parser = Parser()
    parser.test()


def main():
    log.info('Begin `main` function')
    run()
    log.info('end of `main` function')


if __name__ == '__main__':
    main()
