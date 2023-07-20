"""Utilities module."""
from __future__ import annotations

import json
import logging
import re
from base64 import b64decode, b64encode
from collections.abc import Mapping
from datetime import datetime, time, timezone
from typing import Any, TypeVar, cast, overload
from urllib.parse import urljoin as _urljoin
from warnings import warn

_LOGGER = logging.getLogger(__name__)
_T = TypeVar("_T")

ENCODING = "utf-8"
REDACTED = "**REDACTED**"
REDACT_FIELDS = [
    "token",
    "idToken",
    "refreshToken",
    "userId",
    "userEmail",
    "sessionId",
    "oneSignalPlayerId",
    "deviceId",
    "id",
    "litterRobotId",
    "unitId",
    "litterRobotSerial",
    "serial",
]


def decode(value: str) -> str:
    """Decode a value."""
    return b64decode(value).decode(ENCODING)


def encode(value: str | dict) -> str:
    """Encode a value."""
    if isinstance(value, dict):
        value = json.dumps(value)
    return b64encode(value.encode(ENCODING)).decode(ENCODING)


def to_timestamp(timestamp: str | None) -> datetime | None:
    """Construct a UTC offset-aware datetime from a Litter-Robot API timestamp."""
    if not timestamp:
        return None
    if "Z" in timestamp:
        timestamp = timestamp.replace("Z", "")
    if (utc_offset := "+00:00") not in timestamp:
        timestamp += utc_offset
    timestamp = re.sub(r"(\.\d+)", lambda m: m.group().ljust(7, "0")[:7], timestamp)
    return datetime.fromisoformat(timestamp)


def pluralize(word: str, count: int) -> str:
    """Pluralize a word."""
    return f"{count} {word}{'s' if count != 1 else ''}"


def round_time(_datetime: datetime | None = None, round_to: int = 60) -> datetime:
    """Round a datetime to the specified seconds or 1 minute if not specified."""
    if not _datetime:
        _datetime = utcnow()

    return datetime.fromtimestamp(
        (_datetime.timestamp() + round_to / 2) // round_to * round_to, _datetime.tzinfo
    )


def today_at_time(_time: time) -> datetime:
    """Return a datetime representing today at the passed in time."""
    return datetime.combine(utcnow().astimezone(_time.tzinfo), _time)


def urljoin(base: str, subpath_or_url: str | None) -> str:
    """Join a base URL and subpath or URL to form an absolute interpretation of the latter."""
    if not subpath_or_url:
        return base
    if not base.endswith("/"):
        base += "/"
    return _urljoin(base, subpath_or_url)


def utcnow() -> datetime:
    """Return the current UTC offset-aware datetime."""
    return datetime.now(timezone.utc)


def send_deprecation_warning(
    old_name: str, new_name: str | None = None
) -> None:  # pragma: no cover
    """Log a deprecation warning message."""
    message = f"{old_name} has been deprecated{'' if new_name is None else f' in favor of {new_name}'} and will be removed in a future release"
    warn(message, DeprecationWarning, stacklevel=2)
    _LOGGER.warning(message)


@overload
def redact(data: Mapping) -> dict:  # type: ignore[misc]
    ...


@overload
def redact(data: _T) -> _T:
    ...


def redact(data: _T) -> _T:
    """Redact sensitive data in a dict."""
    if not isinstance(data, (Mapping, list)):
        return data

    if isinstance(data, list):
        return cast(_T, [redact(val) for val in data])

    redacted = {**data}

    for key, value in redacted.items():
        if value is None:
            continue
        if isinstance(value, str) and not value:
            continue
        if key in REDACT_FIELDS:
            redacted[key] = REDACTED
        elif isinstance(value, Mapping):
            redacted[key] = redact(value)
        elif isinstance(value, list):
            redacted[key] = [redact(item) for item in value]

    return cast(_T, redacted)

class DictWithStrictDefault(dict):
    """Subclass of built-in dict class. Overrides get() method to provide more strict default values.
    If the key exists in the dictionary and its value is not None, it will return the value.
    If the key does not exist or its value is None, this class will return the provided default value.
    Useful in scenarios when you want to prevent returning None even if a key is present in the dictionary."""
    def get(self, key: str, default: Any = None) -> Any:
        if key in self and self[key] is not None:
            return self[key]
        return default
