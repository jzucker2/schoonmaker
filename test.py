#!/usr/bin/env python3
"""Smoke test: parse sample FDX and log summary."""
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.fdx import FDXParser

set_up_logging()
log = get_logger(__name__)


def main():
    log.info("Begin smoke test")
    file_name = "samples/final_draft_12_sample.fdx"
    log.info("file_name: %s", file_name)
    screenplay = FDXParser().parse(file_name)
    log.info(
        "document_type=%s version=%s scenes=%d",
        screenplay.document_type,
        screenplay.version,
        len(screenplay.scenes),
    )
    log.info("End smoke test")


if __name__ == "__main__":
    main()
