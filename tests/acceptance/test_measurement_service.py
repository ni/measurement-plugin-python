"""Tests to validate measurement service. Uses the Sample Measurement Example."""
import random
import urllib.parse
import urllib.request
from os import path

import grpc
import pytest
from examples.sample_measurement import measurement
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2 as measurement_service_v1_pb2,
    measurement_service_pb2_grpc as measurement_service_v1_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as measurement_service_v2_pb2,
    measurement_service_pb2_grpc as measurement_service_v2_pb2_grpc,
)
from tests.assets import sample_measurement_test_pb2

EXPECTED_PARAMETER_COUNT = 5
EXPECTED_UI_FILE_COUNT = 3


def test___measurement_service___get_metadata_v1_rpc_call___returns_metadata():
    """End to End Test to validate GetMetadata RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with _create_channel(measurement_service_port) as channel:
        stub = measurement_service_v1_pb2_grpc.MeasurementServiceStub(channel)
        get_metadata_response = stub.GetMetadata(measurement_service_v1_pb2.GetMetadataRequest())

    _validate_metadata_response(get_metadata_response)


def test___measurement_service___get_metadata_v2_rpc_call___returns_metadata():
    """End to End Test to validate GetMetadata RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with _create_channel(measurement_service_port) as channel:
        stub = measurement_service_v2_pb2_grpc.MeasurementServiceStub(channel)
        get_metadata_response = stub.GetMetadata(measurement_service_v2_pb2.GetMetadataRequest())

    _validate_metadata_response(get_metadata_response)


@pytest.mark.parametrize(
    "float_in,double_array_in,bool_in,string_in, string_array_in",
    [(0.9, [1.0, 23.56], True, "InputString", ["", "TestString1", "#$%!@<*(&^~`"])],
)
def test___measurement_service___measure_v1_rpc_call___returns_output(
    float_in, double_array_in, bool_in, string_in, string_array_in
):
    """End to End Test to validate Measure RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with _create_channel(measurement_service_port) as channel:
        stub = measurement_service_v1_pb2_grpc.MeasurementServiceStub(channel)
        request = _get_sample_measurement_measure_request_v1(
            float_in, double_array_in, bool_in, string_in, string_array_in
        )
        measure_response = stub.Measure(request)

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, string_array_in
    )
    assert measure_response.outputs.value == serialized_parameter


@pytest.mark.parametrize(
    "float_in,double_array_in,bool_in,string_in, string_array_in",
    [(0.9, [1.0, 23.56], True, "InputString", ["", "TestString1", "#$%!@<*(&^~`"])],
)
def test___measurement_service___measure_v2_rpc_call___returns_output(
    float_in, double_array_in, bool_in, string_in, string_array_in
):
    """End to End Test to validate Measure RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with _create_channel(measurement_service_port) as channel:
        stub = measurement_service_v2_pb2_grpc.MeasurementServiceStub(channel)
        request = _get_sample_measurement_measure_request_v1(
            float_in, double_array_in, bool_in, string_in, string_array_in
        )
        response_iterator = stub.Measure(request)
        responses = [response for response in response_iterator]

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, string_array_in
    )
    assert len(responses) == 1
    assert responses[0].outputs.value == serialized_parameter


@pytest.mark.parametrize("double_array_len", [10000, 100000, 1000000, 10000000])  # up to 80 MB
def test___measurement_service___measure_v1_with_large_array___returns_output(double_array_len):
    """End to End Test to validate Measure RPC call with Sample Measurement."""
    measurement_service_port = _host_service()
    float_in = 1.23
    double_array_in = [random.random() for i in range(double_array_len)]
    bool_in = False
    string_in = "InputString"
    string_array_in = ["", "TestString1", "#$%!@<*(&^~`"]

    with _create_channel(measurement_service_port) as channel:
        stub = measurement_service_v1_pb2_grpc.MeasurementServiceStub(channel)
        request = _get_sample_measurement_measure_request_v1(
            float_in, double_array_in, bool_in, string_in, string_array_in
        )
        measure_response = stub.Measure(request)

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, string_array_in
    )
    assert measure_response.outputs.value == serialized_parameter


def _host_service() -> str:
    measurement.sample_measurement_service.host_service()
    return measurement.sample_measurement_service.grpc_service.port


def _create_channel(port: str):
    return grpc.insecure_channel(
        "localhost:" + port,
        options=[
            ("grpc.max_receive_message_length", -1),
            ("grpc.max_send_message_length", -1),
        ],
    )


def _get_sample_measurement_measure_request_v1(
    float_in, double_array_in, bool_in, string_in, string_array_in
):
    request = measurement_service_v1_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in, double_array_in, bool_in, string_in, string_array_in
        )
    )
    return request


def _get_sample_measurement_measure_request_v2(
    float_in, double_array_in, bool_in, string_in, string_array_in
):
    request = measurement_service_v2_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in, double_array_in, bool_in, string_in, string_array_in
        )
    )
    return request


def _get_configuration_parameters(float_in, double_array_in, bool_in, string_in, string_array_in):
    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, string_array_in
    )
    config_params_any = any_pb2.Any()
    config_params_any.value = serialized_parameter
    return config_params_any


def _get_serialized_measurement_signature(
    float_in, double_array_in, bool_in, string_in, string_array_in
):
    config_params = sample_measurement_test_pb2.SampleMeasurementParameter()
    config_params.float_in = float_in
    config_params.double_array_in.extend(double_array_in)
    config_params.bool_in = bool_in
    config_params.string_in = string_in
    config_params.string_array_in.extend(string_array_in)

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


def _validate_metadata_response(get_metadata_response):
    assert get_metadata_response.measurement_details.display_name == "Sample Measurement (Py)"
    assert get_metadata_response.measurement_details.version == "0.1.0.0"

    assert (
        get_metadata_response.measurement_signature.configuration_parameters_message_type
        == "ni.measurementlink.measurement.v1.MeasurementConfigurations"
    )
    assert (
        get_metadata_response.measurement_signature.outputs_message_type
        == "ni.measurementlink.measurement.v1.MeasurementOutputs"
    )
    assert (
        len(get_metadata_response.measurement_signature.configuration_parameters)
        == EXPECTED_PARAMETER_COUNT
    )
    assert len(get_metadata_response.measurement_signature.outputs) == EXPECTED_PARAMETER_COUNT

    assert len(get_metadata_response.user_interface_details) == EXPECTED_UI_FILE_COUNT
    for details in get_metadata_response.user_interface_details:
        url = urllib.parse.urlparse(details.file_url)
        localpath = urllib.request.url2pathname(url.path)
        assert path.exists(localpath)
