from urllib.parse import urlencode, urlsplit

from decouple import AutoConfig
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.session_management import SessionInitializationBehavior

_INITIALIZATION_BEHAVIOR = {
    SessionInitializationBehavior.AUTO: 0,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION: 1,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION: 2,
    SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH: 3,
    SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE: 4,
}

GRPC_SERVICE_INTERFACE_NAME = "visa_grpc.Visa"
SERVICE_CLASS = "ni.measurementlink.v1.grpcdeviceserver"


def build_visa_grpc_resource_string(
    resource_name: str,
    address: str,
    session_name: str = "",
    initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
) -> str:
    """Build an grpc:// resource string for remoting with NI-VISA."""
    query = {
        "init_behavior": _INITIALIZATION_BEHAVIOR[initialization_behavior],
        "session_name": session_name,
    }
    return f"grpc://{address}/{resource_name}?" + urlencode(query)


def get_visa_grpc_insecure_address(config: AutoConfig, discovery_client: DiscoveryClient) -> str:
    """Get the insecure address of NI gRPC Device Server's VISA interface in host:port format."""
    # Hack: config is a parameter for now so TestStand code modules use the right config path.
    use_grpc_device_server: bool = config(
        "MEASUREMENT_PLUGIN_USE_GRPC_DEVICE_SERVER", default=True, cast=bool
    )
    grpc_device_server_address: str = config(
        "MEASUREMENT_PLUGIN_GRPC_DEVICE_SERVER_ADDRESS", default=""
    )

    if not use_grpc_device_server:
        return ""

    if grpc_device_server_address:
        return urlsplit(grpc_device_server_address).netloc
    else:
        service_location = discovery_client.resolve_service(
            GRPC_SERVICE_INTERFACE_NAME, SERVICE_CLASS
        )
        return service_location.insecure_address
