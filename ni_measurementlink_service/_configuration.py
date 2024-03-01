"""MeasurementLink configuration options."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable, Dict, NamedTuple, TypeVar, Union

from decouple import AutoConfig, Undefined, undefined

from ni_measurementlink_service._dotenvpath import get_dotenv_search_path

if TYPE_CHECKING:
    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


_PREFIX = "MEASUREMENTLINK"

_config = AutoConfig(str(get_dotenv_search_path()))

if TYPE_CHECKING:
    # Work around decouple's lack of type hints.
    _T = TypeVar("_T")

    def _config(
        option: str,
        default: Union[_T, Undefined] = undefined,
        cast: Union[Callable[[str], _T], Undefined] = undefined,
    ) -> _T: ...


# ----------------------------------------------------------------------
# NI Modular Instrument Driver Options
# ----------------------------------------------------------------------
class MIDriverOptions(NamedTuple):
    """Modular instrument driver options."""

    driver_name: str
    """The driver name."""

    simulate: bool = False
    """Specifies whether to simulate session operations."""

    board_type: str = ""
    """The simulated board type (bus)."""

    model: str = ""
    """The simulated instrument model."""

    def update_from_config(self) -> Self:
        """Read options from the configuration file and return a new options object."""
        prefix = f"{_PREFIX}_{self.driver_name.upper()}"
        return self._replace(
            simulate=_config(f"{prefix}_SIMULATE", default=self.simulate, cast=bool),
            board_type=_config(f"{prefix}_BOARD_TYPE", default=self.board_type),
            model=_config(f"{prefix}_MODEL", default=self.model),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a dict to pass to nimi-python."""
        options: Dict[str, Any] = {}
        if self.simulate:
            options["simulate"] = True
        if self.board_type or self.model:
            options["driver_setup"] = {}
            if self.board_type:
                options["driver_setup"]["BoardType"] = self.board_type
            if self.model:
                options["driver_setup"]["Model"] = self.model
        return options


class NISwitchOptions(NamedTuple):
    """NI-SWITCH driver options."""

    driver_name: str
    """The driver name."""

    simulate: bool = False
    """Specifies whether to simulate session operations."""

    topology: str = "Configured Topology"
    """The default topology."""

    def update_from_config(self) -> Self:
        """Read options from the configuration file and return a new options object."""
        prefix = f"{_PREFIX}_{self.driver_name.upper()}"
        return self._replace(
            simulate=_config(f"{prefix}_SIMULATE", default=self.simulate, cast=bool),
            topology=_config(f"{prefix}_TOPOLOGY", default=self.topology),
        )


NIDCPOWER_OPTIONS = MIDriverOptions("nidcpower").update_from_config()
NIDIGITAL_OPTIONS = MIDriverOptions("nidigital").update_from_config()
NIDMM_OPTIONS = MIDriverOptions("nidmm").update_from_config()
NIFGEN_OPTIONS = MIDriverOptions("nifgen").update_from_config()
NISCOPE_OPTIONS = MIDriverOptions("niscope").update_from_config()
NISWITCH_OPTIONS = NISwitchOptions("niswitch").update_from_config()
NISWITCH_MULTIPLEXER_OPTIONS = NISwitchOptions("niswitch_multiplexer").update_from_config()


# ----------------------------------------------------------------------
# NI gRPC Device Server Configuration
# ----------------------------------------------------------------------
USE_GRPC_DEVICE_SERVER: bool = _config(f"{_PREFIX}_USE_GRPC_DEVICE_SERVER", default=True, cast=bool)
GRPC_DEVICE_SERVER_ADDRESS: str = _config(f"{_PREFIX}_GRPC_DEVICE_SERVER_ADDRESS", default="")
