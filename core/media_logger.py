import logging
from pathlib import Path


def get_media_logger(log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("media_manager")
    logger.setLevel(logging.INFO)
    target = Path(log_file) if log_file else Path(__file__).resolve().parents[1] / "logs" / "media_manager.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(target.resolve())
    if not any(isinstance(handler, logging.FileHandler) and handler.baseFilename == resolved for handler in logger.handlers):
        handler = logging.FileHandler(target, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(handler)
    return logger
