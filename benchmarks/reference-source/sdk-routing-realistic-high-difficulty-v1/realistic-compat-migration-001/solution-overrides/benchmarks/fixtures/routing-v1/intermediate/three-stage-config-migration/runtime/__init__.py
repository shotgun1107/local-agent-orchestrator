"""Canonical configuration parsing and serialization."""

from .parser import parse_config
from .serializer import serialize_config

__all__ = ["parse_config", "serialize_config"]
