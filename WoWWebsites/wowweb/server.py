"""Compatibility shim. Prefer wowweb.http."""

from .http import ROOT, STATIC, make_server

__all__ = ["ROOT", "STATIC", "make_server"]
