"""Shared logging, assertion guard and scenario verdicts."""
import json
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
LOGS = ROOT / "logs"

class TestError(Exception):
    """Base for anticipated domain failures."""

def setup(name):
    if not __debug__:
        raise SystemExit("Assertions disabled: remove -O or -OO")
    REPORTS.mkdir(exist_ok=True)
    LOGS.mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())
    logger.propagate = False
    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s")
        for handler in (logging.StreamHandler(),
                        logging.FileHandler(LOGS / f"{name}.log",
                                            mode="w", encoding="utf-8")):
            handler.setFormatter(fmt)
            logger.addHandler(handler)
    return logger

def run_cases(name, cases, check):
    """Each tuple: (label, input, expected exception or None).
    Expected rejection is a PASS; unexpected errors are FAIL.
    """
    log = setup(name)
    results = []
    for label, value, expected in cases:
        log.info("START %s", label)
        log.debug("Input: %r", value)
        error = None
        try:
            check(value)
        except Exception as exc:
            error = exc
        passed = (error is None if expected is None else
                  isinstance(error, expected))
        if passed:
            log.info("PASS %s%s", label,
                     f" (expected {type(error).__name__})" if error else "")
        else:
            log.error("FAIL %s; expected=%s actual=%r", label,
                      expected, error, exc_info=(type(error), error,
                      error.__traceback__) if error else None)
        results.append({"case": label, "verdict": "PASS" if passed else "FAIL",
                        "expected_error": expected.__name__ if expected else None,
                        "actual_error": type(error).__name__ if error else None,
                        "detail": str(error) if error else None})
    path = REPORTS / f"{name}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    log.info("Report: %s", path)
    return int(not all(r["verdict"] == "PASS" for r in results))
