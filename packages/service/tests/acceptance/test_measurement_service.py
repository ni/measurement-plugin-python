"""Tests to validate measurement service. Uses the Sample Measurement Example."""

from __future__ import annotations

import random
import sys
import urllib.parse
import urllib.request
from collections.abc import Generator
from enum import Enum
from os import path

import pytest
from google.protobuf import any_pb2

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2 as v1_measurement_service_pb2,
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from tests.utilities.measurements import loopback_measurement
from tests.utilities.stubs.loopback.types_pb2 import Parameters, ProtobufColor

EXPECTED_PARAMETER_COUNT = 7
EXPECTED_UI_FILE_COUNT = 1


class Color(Enum):
    """Primary colors used for example enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


def test___measurement_service_v1___get_metadata___returns_metadata(
    stub_v1: v1_measurement_service_pb2_grpc.MeasurementServiceStub,
):
    response = stub_v1.GetMetadata(v1_measurement_service_pb2.GetMetadataRequest())

    _validate_get_metadata_response(response)


def test___measurement_service_v2___get_metadata___returns_metadata(
    stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub,
):
    response = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    _validate_get_metadata_response(response)


@pytest.mark.parametrize(
    "float_in,double_array_in,bool_in,string_in,enum_in,protobuf_enum_in,string_array_in",
    [
        (
            0.9,
            [1.0, 23.56],
            True,
            "InputString",
            Color.BLUE,
            ProtobufColor.WHITE,
            ["", "TestString1", "#$%!@<*(&^~`"],
        )
    ],
)
def test___measurement_service_v1___measure___returns_output(
    float_in: float,
    double_array_in: list[float],
    bool_in: bool,
    string_in: str,
    enum_in: Enum,
    protobuf_enum_in: ProtobufColor.ValueType,
    string_array_in: list[str],
    stub_v1: v1_measurement_service_pb2_grpc.MeasurementServiceStub,
):
    metadata = stub_v1.GetMetadata(v1_measurement_service_pb2.GetMetadataRequest())

    request = v1_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in,
            double_array_in,
            bool_in,
            string_in,
            enum_in,
            protobuf_enum_in,
            string_array_in,
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
        )
    )
    response = stub_v1.Measure(request)

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, enum_in, protobuf_enum_in, string_array_in
    )
    assert response.outputs.value == serialized_parameter


@pytest.mark.parametrize(
    "float_in,double_array_in,bool_in,string_in,enum_in,protobuf_enum_in,string_array_in",
    [
        (
            0.9,
            [1.0, 23.56],
            True,
            "InputString",
            Color.BLUE,
            ProtobufColor.WHITE,
            ["", "TestString1", "#$%!@<*(&^~`"],
        )
    ],
)
def test___measurement_service_v2___measure___returns_output(
    float_in: float,
    double_array_in: list[float],
    bool_in: bool,
    string_in: str,
    enum_in: Enum,
    protobuf_enum_in: ProtobufColor.ValueType,
    string_array_in: list[str],
    stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub,
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in,
            double_array_in,
            bool_in,
            string_in,
            enum_in,
            protobuf_enum_in,
            string_array_in,
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
        )
    )
    response_iterator = stub_v2.Measure(request)
    responses = [response for response in response_iterator]

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, enum_in, protobuf_enum_in, string_array_in
    )
    assert len(responses) == 1
    assert responses[0].outputs.value == serialized_parameter


@pytest.mark.parametrize("double_array_len", [10000, 100000, 1000000, 10000000])  # up to 80 MB
def test___measurement_service_v1___measure_with_large_array___returns_output(
    double_array_len: int, stub_v1: v1_measurement_service_pb2_grpc.MeasurementServiceStub
):
    if sys.platform == "win32" and sys.maxsize < 2**32 and double_array_len > 1000000:
        pytest.skip("TODO: 32-bit Python tests fail with out-of-memory errors #818")
    float_in = 1.23
    double_array_in = [random.random() for i in range(double_array_len)]
    bool_in = False
    string_in = "InputString"
    enum_in = Color.BLUE
    protobuf_enum_in = ProtobufColor.WHITE
    string_array_in = ["", "TestString1", "#$%!@<*(&^~`"]
    metadata = stub_v1.GetMetadata(v1_measurement_service_pb2.GetMetadataRequest())

    request = v1_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in,
            double_array_in,
            bool_in,
            string_in,
            enum_in,
            protobuf_enum_in,
            string_array_in,
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
        )
    )
    response = stub_v1.Measure(request)

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, enum_in, protobuf_enum_in, string_array_in
    )
    assert response.outputs.value == serialized_parameter


@pytest.mark.parametrize("double_array_len", [10000, 100000, 1000000, 10000000])  # up to 80 MB
def test___measurement_service_v2___measure_with_large_array___returns_output(
    double_array_len: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    if sys.platform == "win32" and sys.maxsize < 2**32 and double_array_len > 1000000:
        pytest.skip("TODO: 32-bit Python tests fail with out-of-memory errors #818")
    float_in = 1.23
    double_array_in = [random.random() for i in range(double_array_len)]
    bool_in = False
    enum_in = Color.BLUE
    protobuf_enum_in = ProtobufColor.WHITE
    string_in = "InputString"
    string_array_in = ["", "TestString1", "#$%!@<*(&^~`"]
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in,
            double_array_in,
            bool_in,
            string_in,
            enum_in,
            protobuf_enum_in,
            string_array_in,
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
        )
    )
    response_iterator = stub_v2.Measure(request)
    responses = [response for response in response_iterator]

    serialized_parameter = _get_serialized_measurement_signature(
        float_in, double_array_in, bool_in, string_in, enum_in, protobuf_enum_in, string_array_in
    )
    assert len(responses) == 1
    assert responses[0].outputs.value == serialized_parameter


@pytest.fixture(scope="module")
def measurement_service(discovery_service_process) -> Generator[MeasurementService]:
    """Test fixture that creates and hosts a measurement service."""
    with loopback_measurement.measurement_service.host_service() as service:
        yield service


def _get_configuration_parameters(*args, message_type: str = "", **kwargs) -> any_pb2.Any:
    serialized_parameter = _get_serialized_measurement_signature(*args, **kwargs)
    config_params_any = any_pb2.Any()
    config_params_any.type_url = "type.googleapis.com/" + message_type
    config_params_any.value = serialized_parameter
    return config_params_any


def _get_serialized_measurement_signature(
    float_in: float,
    double_array_in: list[float],
    bool_in: bool,
    string_in: str,
    enum_in: Enum,
    protobuf_enum_in: ProtobufColor.ValueType,
    string_array_in: list[str],
) -> bytes:
    config_params = Parameters()
    config_params.float_in = float_in
    config_params.double_array_in.extend(double_array_in)
    config_params.bool_in = bool_in
    config_params.string_in = string_in
    config_params.enum_in = enum_in.value
    config_params.protobuf_enum_in = protobuf_enum_in
    config_params.string_array_in.extend(string_array_in)

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


def _validate_get_metadata_response(
    get_metadata_response: (
        v1_measurement_service_pb2.GetMetadataResponse
        | v2_measurement_service_pb2.GetMetadataResponse
    ),
):
    assert get_metadata_response.measurement_details.display_name == "Loopback Measurement (Py)"
    assert get_metadata_response.measurement_details.version == "1.2.3.4"

    assert (
        get_metadata_response.measurement_signature.configuration_parameters_message_type
        == "ni.tests.LoopbackMeasurement_Python.Configurations"
    )
    assert (
        get_metadata_response.measurement_signature.outputs_message_type
        == "ni.tests.LoopbackMeasurement_Python.Outputs"
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
