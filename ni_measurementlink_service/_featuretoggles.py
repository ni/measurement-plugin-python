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

_PREFIX = "MEASUREMENTLINK"


class CodeReadiness(Enum):
    """Indicates whether code is ready to be supported."""

    RELEASE = 0
    NEXT_RELEASE = 1
    INCOMPLETE = 2
    PROTOTYPE = 3


def _init_code_readiness_level() -> CodeReadiness:
    level = config(
        f"{_PREFIX}_CODE_READINESS_LEVEL", default=CodeReadiness.RELEASE, cast=CodeReadiness
    )
    if (
        config(f"{_PREFIX}_ALLOW_INCOMPLETE", default=False, cast=bool)
        and level.value < CodeReadiness.INCOMPLETE.value
    ):
        level = CodeReadiness.INCOMPLETE
    elif (
        config(f"{_PREFIX}_ALLOW_NEXT_RELEASE", default=False, cast=bool)
        and level.value < CodeReadiness.NEXT_RELEASE.value
    ):
        level = CodeReadiness.NEXT_RELEASE
    return level


# This is not public because `from _featuretoggles import CODE_READINESS_LEVEL`
# is incompatible with the patching performed by the use_code_readiness mark.
_CODE_READINESS_LEVEL = _init_code_readiness_level()


def get_code_readiness_level() -> CodeReadiness:
    """Get the current code readiness level.

    You can override this in tests by specifying the ``use_code_readiness``
    mark.
    """
    return _CODE_READINESS_LEVEL


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
        """Indicates whether the feature is currently enabled.

        You can enable/disable features in tests by specifying the
        ``enable_feature_toggle`` or ``disable_feature_toggle`` marks.
        """
        if self._is_enabled_override is not None:
            return self._is_enabled_override
        return self.readiness.value <= get_code_readiness_level().value

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
    """Decorator specifying that the function requires the specified feature toggle."""

    def decorator(func: Callable[_P, _T]) -> Callable[_P, _T]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
            feature_toggle._raise_if_disabled()
            return func(*args, **kwargs)

        return wrapper

    return decorator
