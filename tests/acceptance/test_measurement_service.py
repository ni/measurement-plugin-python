"""Tests to validate measurement service. Uses the Sample Measurement Example."""
from os import path

import grpc
import pytest
from examples.sample_measurement import measurement
from google.protobuf import any_pb2

from ni_measurement_service._internal.stubs import Measurement_pb2
from ni_measurement_service._internal.stubs import Measurement_pb2_grpc
from ni_measurement_service.measurement.info import UIFileType
from tests.assets import sample_measurement_test_pb2


def test___measurement_service___get_metadata_rpc_call___returns_metadata():
    """End to End Test to validate GetMetadata RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with grpc.insecure_channel("localhost:" + measurement_service_port) as channel:
        stub = Measurement_pb2_grpc.MeasurementServiceStub(channel)
        get_metadata_response = stub.GetMetadata(Measurement_pb2.GetMetadataRequest())

    _validate_metadata_response(get_metadata_response)


@pytest.mark.parametrize(
    "float_in,double_array_in,bool_in,string_in", [(0.9, [1.0, 23.56], True, "InputString")]
)
def test___measurement_service___measure_rpc_call___returns_output(
    float_in, double_array_in, bool_in, string_in
):
    """End to End Test to validate Measure RPC call with Sample Measurement."""
    measurement_service_port = _host_service()

    with grpc.insecure_channel("localhost:" + measurement_service_port) as channel:
        stub = Measurement_pb2_grpc.MeasurementServiceStub(channel)
        request = _get_sample_measurement_measure_request(
            float_in, double_array_in, bool_in, string_in
        )
        measure_response = stub.Measure(request)

    serialized_parameter = _get_serialized_measurement_parameters(
        float_in, double_array_in, bool_in, string_in
    )
    assert measure_response.outputs.value == serialized_parameter


def _host_service() -> int:
    measurement.sample_measurement_service.host_service()
    return str(measurement.sample_measurement_service.grpc_service.port)


def _get_sample_measurement_measure_request(float_in, double_array_in, bool_in, string_in):

    request = Measurement_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            float_in, double_array_in, bool_in, string_in
        )
    )
    return request


def _get_configuration_parameters(float_in, double_array_in, bool_in, string_in):
    serialized_parameter = _get_serialized_measurement_parameters(
        float_in, double_array_in, bool_in, string_in
    )
    config_params_any = any_pb2.Any()
    config_params_any.value = serialized_parameter
    return config_params_any


def _get_serialized_measurement_parameters(float_in, double_array_in, bool_in, string_in):
    config_params = sample_measurement_test_pb2.SampleMeasurementParameter()
    config_params.float_in = float_in
    config_params.double_array_in.extend(double_array_in)
    config_params.bool_in = bool_in
    config_params.string_in = string_in

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


def _validate_metadata_response(get_metadata_response):
    assert get_metadata_response.measurement_details.display_name == "SampleMeasurement"
    assert get_metadata_response.measurement_details.version == "0.1.0.0"
    assert get_metadata_response.measurement_details.measurement_type == "Sample"
    assert get_metadata_response.measurement_details.product_type == "Sample"

    assert (
        get_metadata_response.measurement_parameters.configuration_parameters_messagetype
        == "ni.measurements.v1.MeasurementConfigurations"
    )
    assert (
        get_metadata_response.measurement_parameters.outputs_message_type
        == "ni.measurements.v1.MeasurementOutputs"
    )
    assert len(get_metadata_response.measurement_parameters.configuration_parameters) == 4
    assert len(get_metadata_response.measurement_parameters.outputs) == 4

    url = get_metadata_response.user_interface_details.configuration_ui_url.split("//")
    assert url[0] + "//" == UIFileType.ScreenFile.value
    assert path.exists(url[1])
