import grpc
from measurement_service.stubs import DiscoveryServices_pb2
from measurement_service.stubs import DiscoveryServices_pb2_grpc
from measurement_service.stubs import ServiceLocation_pb2
import measurement_service.framework as framework


_DISCOVERY_SERVICE_ADDRESS = "localhost:42000"
_PROVIDED_MEASUREMENT_SERVICE = "ni.measurements.v1.MeasurementService"
_registration_id = None


def register_measurement_service(service_port: str, service_info: framework.ServiceInfo, display_name: str):
    """Register the Measurement to the Discovery Service.

    Args:
    ----
        port: Port number of the service


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
        request = DiscoveryServices_pb2.RegisterServiceRequest(location=service_location, service_description=service_descriptor)
        request.provided_services.append(_PROVIDED_MEASUREMENT_SERVICE)
        # Registration RPC Call
        register_request = stub.RegisterService(request)
        global _registration_id
        _registration_id = register_request.registration_id
        print("Successfully registered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print("Unable to register with discovery service. Possible reasons : Discovery Service not Available.")
    return None


def unregister_service():
    """Un-Register the Measurement to the Discovery Service."""
    try:
        channel = grpc.insecure_channel(_DISCOVERY_SERVICE_ADDRESS)
        stub = DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)

        # Un-registration Request Creation
        request = DiscoveryServices_pb2.UnregisterServiceRequest(registration_id=_registration_id)
        # Un-registration RPC Call
        stub.UnregisterService(request)
        print("Successfully unregistered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print("Unable to unregister with discovery service. Possible reasons : Discovery Service not Available.")
    return None
