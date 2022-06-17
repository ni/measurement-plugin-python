""" Contains API to register and un-register measurement service with discovery service.
"""
import logging

import grpc

from ni_measurement_service._internal.stubs import DiscoveryServices_pb2
from ni_measurement_service._internal.stubs import DiscoveryServices_pb2_grpc
from ni_measurement_service._internal.stubs import ServiceLocation_pb2
from ni_measurement_service.measurement.info import MeasurementInfo
from ni_measurement_service.measurement.info import ServiceInfo
from ni_measurement_service.measurement.info import UIFileType

_DISCOVERY_SERVICE_ADDRESS = "localhost:42000"
_PROVIDED_MEASUREMENT_SERVICE = "ni.measurements.v1.MeasurementService"
_MEASUREMENT_UI_ATTRIBUTE = "UserInterfaceType=MeasurementUI"
_LABVIEW_ATTRIBUTE = "UserInterfaceType=LabVIEW"

_logger = logging.getLogger(__name__)


class DiscoveryClient:
    """Class that contains APIs need to interact with discovery service.

    Attributes
    ----------
        registryServiceStub (RegistryServiceStub): The gRPC stub to interact with discovery service.

        registration_id(string): The ID from discovery service upon successful registration.

    """

    def __init__(
        self, registry_service_stub: DiscoveryServices_pb2_grpc.RegistryServiceStub = None
    ):
        """Initialise the Discovery Client with provided registry service stub.

        Args:
        ----
            registry_service_stub (RegistryServiceStub, optional):The gRPC stub to interact with
            discovery service.Defaults to None.

        """
        channel = grpc.insecure_channel(_DISCOVERY_SERVICE_ADDRESS)
        self.stub = registry_service_stub or DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)
        self.registration_id = ""

    def register_measurement_service(
        self, service_port: str, service_info: ServiceInfo, measurement_info: MeasurementInfo
    ) -> bool:
        """Register the measurement service with the discovery service.

        Args:
        ----
            service_port (str): Port Number of the measurement service.

            service_info (ServiceInfo): Service Info.

            display_name (str): Display name of the service.

        Returns
        -------
            bool: Boolean to represent if the registration is successful.

        """
        try:

            # Service Location
            service_location = ServiceLocation_pb2.ServiceLocation()
            service_location.location = "localhost"
            service_location.insecure_port = service_port
            # Service Descriptor
            service_descriptor = DiscoveryServices_pb2.ServiceDescriptor()
            service_descriptor.service_id = service_info.service_id
            service_descriptor.name = measurement_info.display_name
            service_descriptor.service_class = service_info.service_class
            service_descriptor.description_url = service_info.description_url
            if measurement_info.ui_file_type is UIFileType.LabVIEW:
                service_descriptor.attributes.append(_LABVIEW_ATTRIBUTE)
            elif measurement_info.ui_file_type is UIFileType.MeasurementUI:
                service_descriptor.attributes.append(_MEASUREMENT_UI_ATTRIBUTE)

            # Registration Request Creation
            request = DiscoveryServices_pb2.RegisterServiceRequest(
                location=service_location, service_description=service_descriptor
            )
            request.provided_services.append(_PROVIDED_MEASUREMENT_SERVICE)
            # Registration RPC Call
            register_response = self.stub.RegisterService(request)
            self.registration_id = register_response.registration_id
            _logger.info("Successfully registered with discovery service.")
        except (grpc._channel._InactiveRpcError):
            _logger.error(
                "Unable to register with discovery service. Possible reason: discovery service not available."
            )
            return False
        except (Exception):
            _logger.exception("Error in registering with discovery service.")
            return False
        return True

    def unregister_service(self) -> bool:
        """Un-registers the measurement service from the discovery service.

        Should be called before the service is closed.

        Returns
        -------
            bool: Boolean to represent if the un-registration is successful.

        """
        try:
            if self.registration_id:
                # Un-registration Request Creation
                request = DiscoveryServices_pb2.UnregisterServiceRequest(
                    registration_id=self.registration_id
                )
                # Un-registration RPC Call
                self.stub.UnregisterService(request)
                _logger.info("Successfully unregistered with discovery service.")
            else:
                _logger.info("Not registered with discovery service.")
        except (grpc._channel._InactiveRpcError):
            _logger.error(
                "Unable to unregister with discovery service. Possible reason: discovery service not available."
            )
            return False
        except (Exception):
            _logger.exception("Error in un-registering with discovery service.")
            return False
        return True
