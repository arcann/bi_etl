import logging


def modify_log_format(log, replace, search='%(message)s'):
    for handler in log.handlers:
        format_str = handler.formatter._fmt
        format_str = format_str.replace(
            search,
            replace
        )
        fmt = logging.Formatter(format_str)
        handler.setFormatter(fmt)
    if log.parent is not None:
        modify_log_format(
            log=log.parent,
            replace=replace,
            search=search
        )