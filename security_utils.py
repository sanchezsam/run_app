# -*- coding: utf-8 -*-
"""Shared hardening helpers for untrusted input handling and HTML rendering."""
import hmac
import html
import os
import re
import xml.etree.ElementTree as ET

import streamlit as st

try:
    from defusedxml.ElementTree import fromstring as _defused_fromstring
except ImportError:
    _defused_fromstring = None

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_TRACK_POINTS = 250_000
ALLOWED_UPLOAD_EXTENSIONS = ("tcx", "gpx", "csv", "fit")

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


class UnsafeInputError(ValueError):
    """Raised when untrusted input fails validation."""


def escape_html(value):
    """Escapes a value for interpolation into an ``unsafe_allow_html`` block."""
    return html.escape(str(value), quote=True)


def sanitize_filename(name, max_length=120):
    """Reduces an uploaded filename to a bare, printable basename."""
    base = os.path.basename(str(name).replace("\\", "/"))
    base = _CONTROL_CHARS.sub("", base).strip().lstrip(".")
    if not base:
        base = "activity"
    return base[:max_length]


def file_extension(name):
    """Returns the lowercase extension of an uploaded filename, without the dot."""
    _, _, ext = sanitize_filename(name).rpartition(".")
    return ext.lower()


def validate_upload(name, payload):
    """Validates an uploaded activity file's extension and size.

    Returns the sanitized filename and its extension, raising
    :class:`UnsafeInputError` when the file must not be parsed.
    """
    safe_name = sanitize_filename(name)
    ext = file_extension(safe_name)
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise UnsafeInputError(
            f"Unsupported file type '.{ext}'. Allowed: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}."
        )
    if not payload:
        raise UnsafeInputError("File is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise UnsafeInputError(
            f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit."
        )
    return safe_name, ext


def parse_xml_safely(payload):
    """Parses untrusted XML without DTD, entity expansion or external references."""
    if _defused_fromstring is not None:
        return _defused_fromstring(payload)

    # Fallback when defusedxml is unavailable: reject any document that carries a
    # DTD, which is what enables entity expansion and external entity resolution.
    probe = payload[:4096]
    if isinstance(probe, bytes):
        probe = probe.decode("utf-8", errors="ignore")
    if "<!DOCTYPE" in probe.upper() or "<!ENTITY" in probe.upper():
        raise UnsafeInputError("XML documents containing a DTD or entities are rejected.")
    return ET.fromstring(payload)


def is_protected_attribute(instance_or_class, key):
    """True when assigning ``key`` from serialized data would shadow app behaviour."""
    if not isinstance(key, str) or not key.isidentifier() or key.startswith("_"):
        return True
    return callable(getattr(instance_or_class, key, None))


def apply_serialized_attributes(instance, data):
    """Assigns dict values onto ``instance``, skipping unsafe/method-shadowing keys."""
    for key, value in data.items():
        if is_protected_attribute(instance, key):
            continue
        try:
            setattr(instance, key, value)
        except Exception:
            continue
    return instance


def validate_coordinate(lat, lon):
    """Validates a WGS-84 coordinate pair, returning it as floats."""
    lat_f, lon_f = float(lat), float(lon)
    if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lon_f <= 180.0):
        raise UnsafeInputError(f"Coordinate out of range: lat={lat_f}, lon={lon_f}.")
    return lat_f, lon_f


def clamp_elevation_m(value, limit=9000.0):
    """Clamps a raw elevation reading (metres) into a physically plausible range."""
    try:
        elevation = float(value)
    except (TypeError, ValueError):
        return 0.0
    if elevation != elevation:  # NaN
        return 0.0
    return max(-limit, min(limit, elevation))


def _configured_access_password():
    """Reads the optional access password from the environment or Streamlit secrets."""
    password = os.environ.get("RUN_APP_PASSWORD", "").strip()
    if password:
        return password
    try:
        return str(st.secrets.get("app_password", "")).strip()
    except Exception:
        return ""


def enforce_access_gate():
    """Blocks the app behind a password when one is configured.

    No-ops when neither ``RUN_APP_PASSWORD`` nor the ``app_password`` Streamlit
    secret is set, so local single-user runs are unaffected. Set one before
    exposing the app on a network: the app itself has no user accounts and every
    visitor otherwise reads and writes the same biometric profile.
    """
    expected = _configured_access_password()
    if not expected:
        return True

    if st.session_state.get("_access_granted"):
        return True

    st.title("🔒 Cardio Training Hub")
    supplied = st.text_input("Access password", type="password", key="_access_password_input")
    if supplied:
        if hmac.compare_digest(supplied, expected):
            st.session_state._access_granted = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
    return False


def sanitize_display_text(value, max_length=200):
    """Strips control characters and truncates free text destined for the UI."""
    text = _CONTROL_CHARS.sub("", str(value))
    return text[:max_length]
