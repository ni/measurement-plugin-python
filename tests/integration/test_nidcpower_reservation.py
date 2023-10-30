import pathlib

import pytest

from ni_measurementlink_service.session_management import (
    PinMapContext,
    SessionManagementClient,
)
from tests.utilities.pin_map_client import PinMapClient


def test___single_session_reserved___initialize_nidcpower_session___single_session_created(
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
    session_management_client: SessionManagementClient,
) -> None:
    pin_map_name = "1Smu1ChannelGroup1Pin1Site.pinmap"
    pin_names = ["Pin1"]
    pin_map_id = pin_map_client.update_pin_map(pin_map_directory / pin_map_name)
    pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
    with session_management_client.reserve_session(
        pin_map_context, pin_names, timeout=0
    ) as reservation:
        with reservation.initialize_nidcpower_session() as session_info:
            assert session_info.session is not None

        assert session_info.session_name == "DCPower1/0"


@pytest.fixture
def pin_map_directory(test_assets_directory: pathlib.Path) -> pathlib.Path:
    """Test fixture that returns the pin map directory."""
    return test_assets_directory / "integration" / "session_management"
