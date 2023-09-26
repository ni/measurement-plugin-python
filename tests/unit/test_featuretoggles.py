from typing import List

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._featuretoggles import (
    READINESS_LEVEL,
    CodeReadiness,
    FeatureNotSupportedError,
    FeatureToggle,
)

RELEASE_FEATURE = FeatureToggle("INCOMPLETE_FEATURE", CodeReadiness.RELEASE)
NEXT_RELEASE_FEATURE = FeatureToggle("NEXT_RELEASE_FEATURE", CodeReadiness.NEXT_RELEASE)
INCOMPLETE_FEATURE = FeatureToggle("INCOMPLETE_FEATURE", CodeReadiness.INCOMPLETE)
PROTOTYPE_FEATURE = FeatureToggle("PROTOTYPE_FEATURE", CodeReadiness.PROTOTYPE)


@PROTOTYPE_FEATURE.required
def _prototype_function(x: int, y: str, z: List[int]) -> str:
    return _prototype_function_impl(x, y, z)


def _prototype_function_impl(x: int, y: str, z: List[int]) -> str:
    return ""


def test___current_readiness_level___is_enabled___reflects_readiness_level() -> None:
    assert RELEASE_FEATURE.is_enabled == (READINESS_LEVEL.value >= CodeReadiness.RELEASE.value)
    assert NEXT_RELEASE_FEATURE.is_enabled == (
        READINESS_LEVEL.value >= CodeReadiness.NEXT_RELEASE.value
    )
    assert INCOMPLETE_FEATURE.is_enabled == (
        READINESS_LEVEL.value >= CodeReadiness.INCOMPLETE.value
    )
    assert PROTOTYPE_FEATURE.is_enabled == (READINESS_LEVEL.value >= CodeReadiness.PROTOTYPE.value)


@pytest.mark.enable_feature_toggle(PROTOTYPE_FEATURE)
def test___feature_toggle_enabled___is_enabled___returns_true() -> None:
    assert PROTOTYPE_FEATURE.is_enabled


@pytest.mark.disable_feature_toggle(PROTOTYPE_FEATURE)
def test___feature_toggle_disabled___is_enabled___returns_false() -> None:
    assert not PROTOTYPE_FEATURE.is_enabled


@pytest.mark.enable_feature_toggle(PROTOTYPE_FEATURE)
def test___feature_toggle_enabled___call_decorated_function___impl_called(
    mocker: MockerFixture,
) -> None:
    impl = mocker.patch("tests.unit.test_featuretoggles._prototype_function_impl")
    impl.return_value = "def"

    result = _prototype_function(123, "abc", [4, 5, 6])

    impl.assert_called_once_with(123, "abc", [4, 5, 6])
    assert result == "def"


@pytest.mark.disable_feature_toggle(PROTOTYPE_FEATURE)
def test___feature_toggle_disabled___call_decorated_function___error_raised(
    mocker: MockerFixture,
) -> None:
    impl = mocker.patch("tests.unit.test_featuretoggles._prototype_function_impl")
    impl.return_value = "def"

    with pytest.raises(FeatureNotSupportedError) as exc_info:
        _ = _prototype_function(123, "abc", [4, 5, 6])

    impl.assert_not_called()
    assert "set MEASUREMENTLINK_ENABLE_PROTOTYPE_FEATURE" in exc_info.value.args[0]
