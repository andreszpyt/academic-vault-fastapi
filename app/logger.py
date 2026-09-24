import logging
import sys
from app.config import LOG_ARQUIVO, LOG_NIVEL

_NIVEIS = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _criar_logger() -> logging.Logger:
    logger = logging.getLogger("cofre_academico")
    nivel  = _NIVEIS.get(LOG_NIVEL.upper(), logging.INFO)
    logger.setLevel(nivel)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(LOG_ARQUIVO, encoding="utf-8")
    fh.setLevel(nivel)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(nivel)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


logger = _criar_logger()