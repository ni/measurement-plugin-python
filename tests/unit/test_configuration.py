from typing import Any, Dict
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._configuration import MIDriverOptions, NISwitchOptions


def test___mi_driver_options___update_from_config___reads_config(config: Mock) -> None:
    config_options = {
        "MEASUREMENTLINK_NIFAKE_SIMULATE": True,
        "MEASUREMENTLINK_NIFAKE_BOARD_TYPE": "PXI",
        "MEASUREMENTLINK_NIFAKE_MODEL": "5678",
    }
    config.side_effect = lambda option, default=None, cast=None: config_options[option]

    options = MIDriverOptions("nifake").update_from_config()

    assert options.simulate
    assert options.board_type == "PXI"
    assert options.model == "5678"


@pytest.mark.parametrize(
    "options,expected_dict",
    [
        (MIDriverOptions("nifake"), {}),
        (
            MIDriverOptions("nifake", True, "", "1234"),
            {"simulate": True, "driver_setup": {"Model": "1234"}},
        ),
        (
            MIDriverOptions("nifake", True, "PXIe", "1234"),
            {"simulate": True, "driver_setup": {"BoardType": "PXIe", "Model": "1234"}},
        ),
    ],
)
def test___mi_driver_options___to_dict___returns_options_dict(
    options: MIDriverOptions, expected_dict: Dict[str, Any]
) -> None:
    assert options.to_dict() == expected_dict


def test___niswitch_options___update_from_config___reads_config(config: Mock) -> None:
    config_options = {
        "MEASUREMENTLINK_NIFAKE_SIMULATE": True,
        "MEASUREMENTLINK_NIFAKE_TOPOLOGY": "5678/Independent",
    }
    config.side_effect = lambda option, default=None, cast=None: config_options[option]

    options = NISwitchOptions("nifake").update_from_config()

    assert options.simulate
    assert options.topology == "5678/Independent"


@pytest.fixture
def config(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock decouple config."""
    return mocker.patch("ni_measurementlink_service._configuration._config")
