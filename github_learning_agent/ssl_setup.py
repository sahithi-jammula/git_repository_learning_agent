"""TLS verification helpers for corporate Windows environments."""

from __future__ import annotations

import os
import ssl
import sys

import certifi


def ssl_verify_context() -> ssl.SSLContext:
    """Return an SSL context httpx / google-genai should use for verify=.

  On Windows, the default context uses the OS certificate store (includes many
  corporate proxy roots). Only pin to a PEM file when SSL_CERT_FILE is set and
  exists — never auto-set SSL_CERT_FILE to certifi, because that *disables* the
  OS store and breaks TLS behind SSL-inspecting proxies.
    """
    cafile = os.environ.get("SSL_CERT_FILE")
    if cafile and os.path.isfile(cafile):
        return ssl.create_default_context(cafile=cafile)
    capath = os.environ.get("SSL_CERT_DIR")
    if capath and os.path.isdir(capath):
        return ssl.create_default_context(capath=capath)
    return ssl.create_default_context()


def configure_ssl_bundle() -> None:
    """Avoid forcing certifi when the OS trust store (Windows) has corporate CAs."""
    use_system = os.environ.get("SSL_USE_SYSTEM_STORE", "").lower() in {"1", "true", "yes"}
    cafile = os.environ.get("SSL_CERT_FILE", "")
    if use_system or (is_windows() and "certifi" in cafile.replace("\\", "/").lower()):
        os.environ.pop("SSL_CERT_FILE", None)
        os.environ.pop("REQUESTS_CA_BUNDLE", None)


def ca_bundle_path() -> str | bool | ssl.SSLContext:
    """Value for httpx verify= — prefer system store on Windows."""
    return ssl_verify_context()


def is_windows() -> bool:
    return sys.platform == "win32"
