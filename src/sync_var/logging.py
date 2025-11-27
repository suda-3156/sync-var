import logging
import sys

from rich.logging import RichHandler


class HaloCompatibleHandler(RichHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # output after clearing the spinner line
        sys.stderr.write("\r\033[K")  # move cursor to start of line and clear line
        sys.stderr.flush()
        super().emit(record)


FORMAT = "%(message)s"

_handler = HaloCompatibleHandler(rich_tracebacks=True)
_handler.setFormatter(logging.Formatter(FORMAT, datefmt="[%X]"))

log = logging.getLogger("sync_var")
log.addHandler(_handler)
log.setLevel(logging.WARNING)


def setup_logging(verbose: bool = False) -> None:
    if verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.WARNING)
