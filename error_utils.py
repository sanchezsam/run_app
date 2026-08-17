# -*- coding: utf-8 -*-
"""Shared error reporting helpers.

Central place for turning caught exceptions into something visible: a log
record with a full traceback and, when a Streamlit script is running, an
on-screen message. Import `get_logger` for module loggers and `report_error`
for failures the user needs to know about (failed saves, unreadable profile
files, aborted imports).
"""
import logging
import os

_LOGGING_CONFIGURED = False

DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name):
    """Returns a module logger, configuring root handlers on first use."""
    global _LOGGING_CONFIGURED
    if not _LOGGING_CONFIGURED:
        logging.basicConfig(
            level=os.environ.get("RUN_APP_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
            format=LOG_FORMAT,
        )
        _LOGGING_CONFIGURED = True
    return logging.getLogger(name)


def report_error(logger, message, exc, show_in_ui=True):
    """Logs `exc` with its traceback and mirrors `message` into the Streamlit UI."""
    logger.error("%s: %s", message, exc, exc_info=exc)
    if not show_in_ui:
        return
    try:
        import streamlit as st

        st.error(f"⚠️ {message}: {exc}")
    except Exception:
        logger.debug("Could not surface the error in the Streamlit UI", exc_info=True)
