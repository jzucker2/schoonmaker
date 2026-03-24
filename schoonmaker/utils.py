import logging


def strip_run_varying_ids(val: object) -> object:
    """
    Recursively remove ``id`` and ``dual_group`` from dicts.

    Used by parse checksums and by ``parse_json_diff`` scene digests so both
    stay aligned.
    """
    if isinstance(val, dict):
        out = dict(val)
        out.pop("id", None)
        out.pop("dual_group", None)
        return {k: strip_run_varying_ids(v) for k, v in out.items()}
    if isinstance(val, list):
        return [strip_run_varying_ids(item) for item in val]
    return val


def set_up_logging(level=logging.DEBUG):
    format = "[%(levelname)s] %(asctime)s %(message)s"
    logging.basicConfig(format=format, level=level)


# pass in __name__
def get_logger(name):
    return logging.getLogger(name)
