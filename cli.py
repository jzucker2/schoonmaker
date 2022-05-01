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
    file_name = cli_args.file
    log.info(f'got cli file_name: {file_name}')
    parser.naive_parse(file_name)
    log.info('done with `run`')


def main():
    log.info('Begin `main` function')
    run()
    log.info('end of `main` function')


if __name__ == '__main__':
    main()
