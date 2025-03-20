import logging
import pathlib
import re
from collections.abc import Generator

import pytest
from pytest import FixtureRequest, LogCaptureFixture

from ni_measurement_plugin_sdk_service import session_management
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import SessionManagementClient
from tests.acceptance.test_streaming_data_measurement import (
    _get_configuration_parameters as get_streaming_data_configuration_parameters,
)
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import (
    loopback_measurement,
    streaming_data_measurement,
)


def test___discovery_client___call___client_call_logged(
    caplog: LogCaptureFixture, discovery_client: DiscoveryClient
) -> None:
    with caplog.at_level(logging.DEBUG):
        _ = discovery_client.resolve_service(
            session_management.GRPC_SERVICE_INTERFACE_NAME, session_management.GRPC_SERVICE_CLASS
        )

    method_name = "/ni.measurementlink.discovery.v1.DiscoveryService/ResolveService"
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert f"gRPC client call starting: {method_name}" in debug_messages
    assert f"gRPC client call complete: {method_name}" in debug_messages


def test___pin_map_client___call___client_call_logged(
    caplog: LogCaptureFixture,
    pin_map_client: PinMapClient,
    pin_map_directory: pathlib.Path,
) -> None:
    with caplog.at_level(logging.DEBUG):
        pin_map_path = pin_map_directory / "1Smu1ChannelGroup2Pin2Site.pinmap"
        _ = pin_map_client.update_pin_map(pin_map_path)

    method_name = "/ni.measurementlink.pinmap.v1.PinMapService/UpdatePinMapFromXml"
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert f"gRPC client call starting: {method_name}" in debug_messages
    assert f"gRPC client call complete: {method_name}" in debug_messages


def test___session_management_client___call___client_call_logged(
    caplog: LogCaptureFixture, request: FixtureRequest
) -> None:
    with caplog.at_level(logging.DEBUG):
        # HACK: set log level before constructing client
        session_management_client: SessionManagementClient = request.getfixturevalue(
            "session_management_client"
        )

        session_management_client.unregister_sessions(session_info=[])

    method_name = (
        "/ni.measurementlink.sessionmanagement.v1.SessionManagementService/UnregisterSessions"
    )
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert f"gRPC client call starting: {method_name}" in debug_messages
    assert f"gRPC client call complete: {method_name}" in debug_messages


@pytest.mark.service_class("ni.tests.LoopbackMeasurement_Python")
def test___loopback_measurement___get_metadata___server_call_logged(
    caplog: LogCaptureFixture, request: FixtureRequest
) -> None:
    with caplog.at_level(logging.DEBUG):
        # HACK: set log level before constructing server
        stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub = request.getfixturevalue(
            "stub_v2"
        )

        _ = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    method_name = "/ni.measurementlink.measurement.v2.MeasurementService/GetMetadata"
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert f"gRPC server call starting: {method_name}" in debug_messages
    assert f"gRPC server call complete: {method_name}" in debug_messages
    info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    info_regex = re.compile(rf"gRPC server call {method_name} responded OK in [\d.]+ ms")
    assert len(list(filter(info_regex.match, info_messages))) == 1


@pytest.mark.service_class("ni.tests.StreamingDataMeasurement_Python")
def test___streaming_data_measurement___measure___server_call_logged(
    caplog: LogCaptureFixture, request: FixtureRequest
) -> None:
    with caplog.at_level(logging.DEBUG):
        # HACK: set log level before constructing server
        stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub = request.getfixturevalue(
            "stub_v2"
        )
        num_responses = 10
        metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

        measure_request = v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=get_streaming_data_configuration_parameters(
                message_type=metadata.measurement_signature.configuration_parameters_message_type,
                num_responses=num_responses,
            )
        )
        response_iterator = stub_v2.Measure(measure_request)
        for response in response_iterator:
            pass

    method_name = "/ni.measurementlink.measurement.v2.MeasurementService/Measure"
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert f"gRPC server call starting: {method_name}" in debug_messages
    assert f"gRPC server call complete: {method_name}" in debug_messages
    debug_response_regex = re.compile(rf"gRPC server call streaming response: {method_name}")
    assert len(list(filter(debug_response_regex.match, debug_messages))) == num_responses
    info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
    info_regex = re.compile(rf"gRPC server call {method_name} responded OK in [\d.]+ ms")
    assert len(list(filter(info_regex.match, info_messages))) == 1


@pytest.fixture
def measurement_service(request: FixtureRequest) -> MeasurementService:
    service_class_marker = request.node.get_closest_marker("service_class")
    service_class = service_class_marker.args[0]
    if service_class == "ni.tests.LoopbackMeasurement_Python":
        return request.getfixturevalue("loopback_measurement_service")
    elif service_class == "ni.tests.StreamingDataMeasurement_Python":
        return request.getfixturevalue("streaming_data_measurement_service")
    else:
        raise ValueError(f"Unsupported service class: {service_class}")


@pytest.fixture
def loopback_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates a loopback measurement."""
    with loopback_measurement.measurement_service.host_service() as service:
        yield service


@pytest.fixture
def streaming_data_measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates a loopback measurement."""
    with streaming_data_measurement.measurement_service.host_service() as service:
        yield service
