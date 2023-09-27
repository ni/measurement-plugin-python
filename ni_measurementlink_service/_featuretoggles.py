from __future__ import annotations

import functools
import sys
from enum import Enum
from typing import TYPE_CHECKING, Callable, TypeVar

from decouple import config

if TYPE_CHECKING:
    if sys.version_info >= (3, 10):
        from typing import ParamSpec
    else:
        from typing_extensions import ParamSpec

    _P = ParamSpec("_P")
    _T = TypeVar("_T")


class CodeReadiness(Enum):
    """Indicates whether code is ready to be supported."""

    RELEASE = 0
    NEXT_RELEASE = 1
    INCOMPLETE = 2
    PROTOTYPE = 3


class FeatureNotSupportedError(Exception):
    """The feature is not supported at the current code readiness level."""


class FeatureToggle:
    """A run-time feature toggle."""

    name: str
    """The name of the feature."""

    readiness: CodeReadiness
    """The code readiness at which this feature is enabled."""

    def __init__(self, name: str, readiness: CodeReadiness) -> None:
        """Initialize the feature toggle."""
        assert name == name.upper()
        self.name = name
        self.readiness = readiness
        self._is_enabled_override = None
        # Only read the env var at initialization time.
        if config(f"{_PREFIX}_ENABLE_{name}", default=False, cast=bool):
            self._is_enabled_override = True

    @property
    def is_enabled(self) -> bool:
        """Indicates whether the feature is currently enabled."""
        if self._is_enabled_override is not None:
            return self._is_enabled_override
        return self.readiness.value <= READINESS_LEVEL.value

    def _raise_if_disabled(self) -> None:
        if self.is_enabled:
            return

        env_vars = f"{_PREFIX}_ENABLE_{self.name}"
        if self.readiness in [CodeReadiness.NEXT_RELEASE, CodeReadiness.INCOMPLETE]:
            env_vars += f" or {_PREFIX}_ALLOW_{self.readiness.name}"
        message = (
            f"The {self.name} feature is not supported at the current code readiness level. "
            f" To enable it, set {env_vars}."
        )
        raise FeatureNotSupportedError(message)


def requires_feature(
    feature_toggle: FeatureToggle,
) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    """Function decorator specifying a required feature toggle."""

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            feature_toggle._raise_if_disabled()
            return func(*args, **kwargs)

        return wrapper

    return decorator


_PREFIX = "MEASUREMENTLINK"
_ALLOW_INCOMPLETE: bool = config(f"{_PREFIX}_ALLOW_INCOMPLETE", default=False, cast=bool)
_ALLOW_NEXT_RELEASE: bool = config(f"{_PREFIX}_ALLOW_NEXT_RELEASE", default=False, cast=bool)

if _ALLOW_INCOMPLETE:
    READINESS_LEVEL = CodeReadiness.INCOMPLETE
elif _ALLOW_NEXT_RELEASE:
    READINESS_LEVEL = CodeReadiness.NEXT_RELEASE
else:
    READINESS_LEVEL = CodeReadiness.RELEASE
