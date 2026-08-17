# -*- coding: utf-8 -*-
"""Checks for the input-hardening helpers. Run with: python test_security_utils.py"""
from models import Character
from security_utils import (
    UnsafeInputError,
    clamp_elevation_m,
    escape_html,
    parse_xml_safely,
    sanitize_filename,
    validate_coordinate,
    validate_upload,
)

XXE = (
    b'<?xml version="1.0"?><!DOCTYPE gpx [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
    b'<gpx><name>&x;</name></gpx>'
)


def check(label, condition):
    assert condition, label
    print(f"ok: {label}")


def main():
    check("path traversal stripped", sanitize_filename("../../etc/passwd.gpx") == "passwd.gpx")
    check("null bytes stripped", "\x00" not in sanitize_filename("run\x00.gpx"))

    check("valid upload accepted", validate_upload("run.gpx", b"<gpx/>") == ("run.gpx", "gpx"))
    for name, payload in (("run.exe", b"x"), ("run.gpx", b""), ("run.gpx", b"x" * (26 * 1024 * 1024))):
        try:
            validate_upload(name, payload)
            raise AssertionError(f"upload should have been rejected: {name}")
        except UnsafeInputError:
            pass
    print("ok: bad extension, empty and oversized uploads rejected")

    try:
        parse_xml_safely(XXE)
        raise AssertionError("XXE payload should have been rejected")
    except Exception:
        print("ok: external entity payload rejected")

    check("coordinates parsed", validate_coordinate("42.5", "-71.2") == (42.5, -71.2))
    for lat, lon in (("91", "0"), ("0", "181"), ("nan", "0")):
        try:
            validate_coordinate(lat, lon)
            raise AssertionError(f"coordinate should have been rejected: {lat},{lon}")
        except (UnsafeInputError, ValueError):
            pass
    print("ok: out-of-range coordinates rejected")

    check("elevation clamped", clamp_elevation_m("1e9") == 9000.0)
    check("elevation garbage neutralised", clamp_elevation_m("<script>") == 0.0)

    char = Character.from_dict({"gold": 25, "to_dict": "pwned", "__dict__": {}, "_secret": 1})
    check("method not shadowed", callable(char.to_dict))
    check("private key skipped", not hasattr(char, "_secret"))
    check("normal field applied", char.gold == 25)

    check("html escaped", escape_html("<img src=x onerror=alert(1)>").startswith("&lt;img"))
    print("\nall security checks passed")


if __name__ == "__main__":
    main()
