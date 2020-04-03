import logging

__all__ = ["toggle_debug_logging"]


def toggle_debug_logging(enabled: int) -> None:
    logging.basicConfig(level=logging.DEBUG if enabled else logging.WARNING, force=True)  # type: ignore
