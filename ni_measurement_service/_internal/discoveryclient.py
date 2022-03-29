""" Contains API to register and un-register measurement service with discovery service.
"""
import grpc

from ni_measurement_service._internal.stubs import DiscoveryServices_pb2
from ni_measurement_service._internal.stubs import DiscoveryServices_pb2_grpc
from ni_measurement_service._internal.stubs import ServiceLocation_pb2
from ni_measurement_service.measurement.info import ServiceInfo


_DISCOVERY_SERVICE_ADDRESS = "localhost:42000"
_PROVIDED_MEASUREMENT_SERVICE = "ni.measurements.v1.MeasurementService"
_registration_id = None


def register_measurement_service(
    service_port: str, service_info: ServiceInfo, display_name: str
) -> None:
    """Register the measurement service with the discovery service.

    Args:
    ----
        service_port (str): Port Number of the measurement service.
        service_info (ServiceInfo): Service Info.
        display_name (str): Display name of the service.

    """
    try:
        channel = grpc.insecure_channel(_DISCOVERY_SERVICE_ADDRESS)
        stub = DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)
        # Service Location
        service_location = ServiceLocation_pb2.ServiceLocation()
        service_location.location = "localhost"
        service_location.insecure_port = str(service_port)
        # Service Descriptor
        service_descriptor = DiscoveryServices_pb2.ServiceDescriptor()
        service_descriptor.service_id = service_info.service_id
        service_descriptor.name = display_name
        service_descriptor.service_class = service_info.service_class
        service_descriptor.description_url = service_info.description_url
        # Registration Request Creation
        request = DiscoveryServices_pb2.RegisterServiceRequest(
            location=service_location, service_description=service_descriptor
        )
        request.provided_services.append(_PROVIDED_MEASUREMENT_SERVICE)
        # Registration RPC Call
        register_request = stub.RegisterService(request)
        global _registration_id
        _registration_id = register_request.registration_id
        print("Successfully registered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to register with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None


def unregister_service():
    """Un-registers the measurement service from the discovery service.

    Should be called before the service is closed.

    """
    try:
        channel = grpc.insecure_channel(_DISCOVERY_SERVICE_ADDRESS)
        stub = DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)

        # Un-registration Request Creation
        request = DiscoveryServices_pb2.UnregisterServiceRequest(registration_id=_registration_id)
        # Un-registration RPC Call
        stub.UnregisterService(request)
        print("Successfully unregistered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to unregister with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None
