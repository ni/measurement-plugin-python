"""Client for accessing the NI Discovery Service."""

from __future__ import annotations

import logging
import threading
from collections.abc import Sequence

import grpc
from deprecation import deprecated

from ni_measurement_plugin_sdk_service._annotations import (
    SERVICE_PROGRAMMINGLANGUAGE_KEY,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.discovery.v1 import (
    discovery_service_pb2,
    discovery_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery._support import (
    _get_discovery_service_address,
)
from ni_measurement_plugin_sdk_service.discovery._types import (
    ComputeNodeDescriptor,
    ServiceLocation,
)
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.info import (
    MeasurementInfo,
    ServiceInfo,
)

_logger = logging.getLogger(__name__)


class DiscoveryClient:
    """Client for accessing the NI Discovery Service."""

    def __init__(
        self,
        stub: discovery_service_pb2_grpc.DiscoveryServiceStub | None = None,
        *,
        grpc_channel_pool: GrpcChannelPool | None = None,
    ) -> None:
        """Initialize the discovery client.

        Args:
            stub: An optional discovery service gRPC stub for unit testing.

            grpc_channel_pool: An optional gRPC channel pool (recommended).
        """
        self._initialization_lock = threading.Lock()
        self._grpc_channel_pool = grpc_channel_pool
        self._stub = stub
        self._registration_id = ""

    @property
    @deprecated(
        deprecated_in="1.2.0-dev2",
        details="This property should not be public and will be removed in a later release.",
    )
    def registration_id(self) -> str:
        """ "The ID from discovery service upon successful registration."""
        return self._registration_id

    @property
    @deprecated(
        deprecated_in="1.2.0-dev2",
        details="This property should not be public and will be removed in a later release.",
    )
    def stub(self) -> discovery_service_pb2_grpc.DiscoveryServiceStub:
        """Get the gRPC stub used to interact with the discovery service."""
        return self._get_stub()

    def _get_stub(self) -> discovery_service_pb2_grpc.DiscoveryServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    _logger.debug("Creating unshared GrpcChannelPool.")
                    self._grpc_channel_pool = GrpcChannelPool()
                if self._stub is None:
                    address = _get_discovery_service_address()
                    channel = self._grpc_channel_pool.get_channel(address)
                    self._stub = discovery_service_pb2_grpc.DiscoveryServiceStub(channel)
        return self._stub

    @deprecated(deprecated_in="1.2.0-dev2", details="Use register_service instead.")
    def register_measurement_service(
        self, service_port: str, service_info: ServiceInfo, measurement_info: MeasurementInfo
    ) -> bool:
        """Register the measurement service with the discovery service.

        Args:
            service_port: The port number of the service.

            service_info: Information describing the service.

            measurement_info: Information describing the measurement.

        Returns:
            Boolean indicating whether the service was successfully registered.
        """
        if self._registration_id:
            raise RuntimeError("Service already registered")

        service_location = ServiceLocation(
            location="localhost",
            insecure_port=service_port,
            ssl_authenticated_port="",
        )

        self._registration_id = self.register_service(
            service_info._replace(display_name=measurement_info.display_name),
            service_location,
        )
        return True

    def register_service(self, service_info: ServiceInfo, service_location: ServiceLocation) -> str:
        """Register the specified service with the discovery service.

        Args:
            service_info: Information describing the service.

            service_location: The location of the service on the network.

        Returns:
            ID that can be used to unregister the service.
        """
        annotations = service_info.annotations.copy()
        annotations[SERVICE_PROGRAMMINGLANGUAGE_KEY] = "Python"
        try:
            grpc_service_description = discovery_service_pb2.ServiceDescriptor(
                display_name=service_info.display_name,
                description_url=service_info.description_url,
                provided_interfaces=service_info.provided_interfaces,
                service_class=service_info.service_class,
                annotations=annotations,
                versions=service_info.versions,
            )

            grpc_service_location = discovery_service_pb2.ServiceLocation(
                location=service_location.location,
                insecure_port=service_location.insecure_port,
                ssl_authenticated_port=service_location.ssl_authenticated_port,
            )

            request = discovery_service_pb2.RegisterServiceRequest(
                service_description=grpc_service_description,
                location=grpc_service_location,
            )

            response = self._get_stub().RegisterService(request)
            _logger.info("Successfully registered with discovery service.")
            return response.registration_id
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to register with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in registering with discovery service.")
            raise
        except FileNotFoundError:
            _logger.error(
                "Unable to register with discovery service. Possible reason: discovery service not running."
            )
            raise
        except Exception:
            _logger.exception("Error in registering with discovery service.")
            raise

    def unregister_service(self, registration_id: str = "") -> bool:
        """Unregisters the specified service from the discovery service.

        This method should be called before the service exits.

        Args:
            registration_id: The registration ID returned from register_service.
                This argument should be omitted after calling the deprecated
                register_measurement_service method.

        Returns:
            Boolean indicating whether the service was unregistered.
        """
        try:
            if not registration_id:
                registration_id = self._registration_id
                if not registration_id:
                    _logger.info("Not registered with discovery service.")
                    return False

            request = discovery_service_pb2.UnregisterServiceRequest(
                registration_id=registration_id
            )

            _ = self._get_stub().UnregisterService(request)
            _logger.info("Successfully unregistered with discovery service.")

            if registration_id == self._registration_id:
                self._registration_id = ""

            return True
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                _logger.error(
                    "Unable to unregister with discovery service. Possible reason: discovery service not available."
                )
            else:
                _logger.exception("Error in unregistering with discovery service.")
            raise
        except FileNotFoundError:
            _logger.error(
                "Unable to unregister with discovery service. Possible reason: discovery service not running."
            )
            raise
        except Exception:
            _logger.exception("Error in unregistering with discovery service.")
            raise

    def resolve_service(
        self,
        provided_interface: str,
        service_class: str = "",
        deployment_target: str = "",
        version: str = "",
    ) -> ServiceLocation:
        """Resolve the location of a service.

        Given a description of a service, returns information that can be used to establish
        communication with that service. If necessary, the service will be started by the
        discovery service if it has not already been started.

        Args:
            provided_interface: The gRPC full name of the service.
            service_class: The service "class" that should be matched. If the value is not
                specified and there is more than one matching service registered, an error
                is returned.
            deployment_target: The deployment target from which the service should be resolved.
            version: The version of the service to resolve. If not specified, the latest version
                will be resolved.

        Returns:
            The service location.
        """
        request = discovery_service_pb2.ResolveServiceRequest(
            provided_interface=provided_interface,
            service_class=service_class,
            deployment_target=deployment_target,
            version=version,
        )

        response = self._get_stub().ResolveService(request)

        return ServiceLocation._from_grpc(response)

    def resolve_service_with_information(
        self,
        provided_interface: str,
        service_class: str = "",
        deployment_target: str = "",
        version: str = "",
    ) -> tuple[ServiceLocation, ServiceInfo]:
        """Resolve the location of a service along with its information.

        Given a description of a service, returns information for the service in addition to
        the location of the service. If necessary, the service will be started by the discovery
        service if it has not already been started.

        Args:
            provided_interface: The gRPC full name of the service.
            service_class: The service "class" that should be matched. If the value is not
                specified and there is more than one matching service registered, an error
                is returned.
            deployment_target: The deployment target from which the service should be resolved.
            version: The version of the service to resolve. If not specified, the latest version
                will be resolved.

        Returns:
            A tuple containing the service location and service information.
        """
        request = discovery_service_pb2.ResolveServiceWithInformationRequest(
            provided_interface=provided_interface,
            service_class=service_class,
            deployment_target=deployment_target,
            version=version,
        )

        response = self._get_stub().ResolveServiceWithInformation(request)

        return (
            ServiceLocation._from_grpc(response.service_location),
            ServiceInfo._from_grpc(response.service_descriptor),
        )

    def enumerate_services(self, provided_interface: str) -> Sequence[ServiceInfo]:
        """Enumerates all the services for the provided interface.

        Args:
            provided_interface: The gRPC full name of the services.

        Returns:
            The list of information describing the services.
        """
        request = discovery_service_pb2.EnumerateServicesRequest(
            provided_interface=provided_interface
        )

        response = self._get_stub().EnumerateServices(request)

        return [ServiceInfo._from_grpc(service) for service in response.available_services]

    def enumerate_compute_nodes(self) -> Sequence[ComputeNodeDescriptor]:
        """Enumerates all the compute nodes registered with the discovery service.

        Returns:
            The list of information describing the compute nodes.
        """
        request = discovery_service_pb2.EnumerateComputeNodesRequest()

        try:
            response = self._get_stub().EnumerateComputeNodes(request)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNIMPLEMENTED:
                return []
            raise

        return [ComputeNodeDescriptor._from_grpc(node) for node in response.compute_nodes]
