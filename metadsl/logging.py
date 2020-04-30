from __future__ import annotations
import logging
import dataclasses
import typing

__all__ = ["toggle_debug_logging", "CaptureLogging"]


def metadsl_filter(record: logging.LogRecord) -> bool:
    """
    Only allow through if in metadsl
    """
    return record.name.startswith("metadsl")


handler = logging.StreamHandler()
handler.addFilter(metadsl_filter)


def toggle_debug_logging(enabled: bool) -> None:
    logging.basicConfig(  # type: ignore
        level=logging.DEBUG if enabled else logging.WARNING,
        force=True,
        handlers=[handler],
    )


class CapturingHandler(logging.Handler):
    """
    A logging handler capturing all (raw and formatted) logging output.
    """

    def __init__(self, events: typing.List[str]):
        super().__init__()
        self.events = events

    def emit(self, record):
        self.events.append(logging.Formatter("%(name)s: %(message)s").format(record))


@dataclasses.dataclass
class CaptureLogging:
    """
    Capture all logging.

        with CaputureLogging() as results:
            ...
        # results contains a list of all log messages, formatted
    

    Some inspiration from unittest.assertLogs
    """

    events: typing.List[str] = dataclasses.field(default_factory=list)
    old_handlers: typing.List[logging.Handler] = dataclasses.field(init=False)

    def __enter__(self):
        self.old_handlers = logging.root.handlers
        logging.root.handlers = [CapturingHandler(self.events)]
        return self.events

    def __exit__(self, et, ev, tb):
        logging.root.handlers = self.old_handlers
