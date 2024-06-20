import logging

from _visa_dmm import Session
from _visa_grpc import build_visa_grpc_resource_string, get_visa_grpc_insecure_address
from decouple import AutoConfig
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.session_management import (
    SessionInformation,
    SessionInitializationBehavior,
)

_logger = logging.getLogger(__name__)


class VisaDmmSessionConstructor:
    """Measurement plug-in constructor for VISA DMM sessions."""

    def __init__(
        self,
        config: AutoConfig,
        discovery_client: DiscoveryClient,
        initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    ) -> None:
        """Construct a VisaDmmSessionConstructor."""
        self._config = config
        self._discovery_client = discovery_client
        self._initialization_behavior = initialization_behavior

        # Hack: config is a parameter for now so TestStand code modules use the right config path.
        self._visa_dmm_simulate: bool = config(
            "MEASUREMENT_PLUGIN_VISA_DMM_SIMULATE", default=False, cast=bool
        )

        if self._visa_dmm_simulate:
            # _visa_dmm_sim.yaml doesn't include the grpc:// resource names.
            _logger.debug("Not using NI gRPC Device Server due to simulation")
            self._address = ""
        else:
            self._address = get_visa_grpc_insecure_address(config, discovery_client)
            if self._address:
                _logger.debug("NI gRPC Device Server address: http://%s", self._address)
            else:
                _logger.debug("Not using NI gRPC Device Server")

    def __call__(self, session_info: SessionInformation) -> Session:
        """Construct a VISA DMM session based on measurement plug-in info."""
        resource_name = session_info.resource_name
        if self._address:
            resource_name = build_visa_grpc_resource_string(
                resource_name,
                self._address,
                session_info.session_name,
                self._initialization_behavior,
            )

        # When this measurement is called from outside of TestStand (session_exists
        # == False), reset the instrument to a known state. In TestStand,
        # ProcessSetup resets the instrument.
        reset_device = not session_info.session_exists

        _logger.debug("VISA resource name: %s", resource_name)
        return Session(resource_name, reset_device=reset_device, simulate=self._visa_dmm_simulate)
