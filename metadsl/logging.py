import logging

__all__ = ["toggle_debug_logging"]


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
