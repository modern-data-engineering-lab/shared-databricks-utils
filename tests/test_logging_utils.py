from __future__ import annotations

import logging

from databricks_utils.logging_utils import get_logger


def test_get_logger_sets_level_and_handler() -> None:
    logger = get_logger("test.logger.level", level=logging.DEBUG)

    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert logger.propagate is False


def test_get_logger_does_not_duplicate_handlers_on_repeat_calls() -> None:
    first = get_logger("test.logger.repeat")
    second = get_logger("test.logger.repeat")

    assert first is second
    assert len(second.handlers) == 1


def test_get_logger_emits_formatted_message(capsys) -> None:
    logger = get_logger("test.logger.emit", level=logging.INFO)

    logger.info("hello world")

    captured = capsys.readouterr()
    assert "test.logger.emit" in captured.out
    assert "hello world" in captured.out
    assert "INFO" in captured.out
