"""Tests to validate a v2 measurement service that streams data."""

from __future__ import annotations

from collections.abc import Generator

import grpc
import pytest
from google.protobuf import any_pb2

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from tests.utilities.measurements import streaming_data_measurement
from tests.utilities.stubs.streamingdata.types_pb2 import Configurations, Outputs


@pytest.mark.parametrize("num_responses", [1, 10, 100])
def test___streaming_measurement_service___request_number_of_responses___receives_responses(
    num_responses: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
            num_responses=num_responses,
        )
    )

    response_iterator = stub_v2.Measure(request)

    responses = [response for response in response_iterator]
    assert len(responses) == num_responses


@pytest.mark.parametrize("data_size", [1, 10, 100])
def test___streaming_measurement_service___request_data_cumulatively___receives_expected_amount_of_data(
    data_size: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    name = "testing-cumulative"
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
            name=name,
            data_size=data_size,
            cumulative_data=True,
        )
    )

    response_iterator = stub_v2.Measure(request)

    expected_data: list[int] = []
    index = 0
    for response in response_iterator:
        expected_data.extend(index for i in range(data_size))
        expected = _get_serialized_measurement_outputs(name, index, expected_data)
        assert expected == response.outputs.value
        index += 1


@pytest.mark.parametrize("data_size", [1, 10, 100])
def test___streaming_measurement_service___specify_data_size___receives_expected_amount_of_data(
    data_size: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    name = "testing-not-cumulative"
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
            name=name,
            data_size=data_size,
            cumulative_data=False,
        )
    )

    response_iterator = stub_v2.Measure(request)

    index = 0
    for response in response_iterator:
        expected_data = [index for i in range(data_size)]
        expected = _get_serialized_measurement_outputs(name, index, expected_data)
        assert expected == response.outputs.value
        index += 1


@pytest.mark.parametrize("error_on_index", [1, 5, 9])
def test___streaming_measurement_service___specify_error_index___errors_at_expected_response(
    error_on_index: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())

    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            message_type=metadata.measurement_signature.configuration_parameters_message_type,
            error_on_index=error_on_index,
        )
    )

    response_iterator = stub_v2.Measure(request)

    with pytest.raises(grpc.RpcError, match=f"Errored at index {error_on_index}"):
        for index, response in enumerate(response_iterator):
            pass
    assert (index + 1) == error_on_index


def _get_configuration_parameters(*args, message_type: str = "", **kwargs) -> any_pb2.Any:
    serialized_parameter = _get_serialized_measurement_configuration_parameters(*args, **kwargs)
    config_params_any = any_pb2.Any()
    config_params_any.type_url = "type.googleapis.com/" + message_type
    config_params_any.value = serialized_parameter
    return config_params_any


def _get_serialized_measurement_configuration_parameters(
    name: str = "test",
    num_responses: int = 10,
    data_size: int = 1,
    cumulative_data: bool = True,
    response_interval_in_ms: int = 1,
    error_on_index: int = -1,
) -> bytes:
    config_params = Configurations()
    config_params.name = name
    config_params.num_responses = num_responses
    config_params.data_size = data_size
    config_params.cumulative_data = cumulative_data
    config_params.response_interval_in_ms = response_interval_in_ms
    config_params.error_on_index = error_on_index

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


def _get_serialized_measurement_outputs(
    name: str,
    index: int,
    data: list[int],
) -> bytes:
    config_params = Outputs()
    config_params.name = name
    config_params.index = index
    config_params.data.extend(data)

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


@pytest.fixture(scope="module")
def measurement_service(discovery_service_process) -> Generator[MeasurementService]:
    """Test fixture that creates and hosts a measurement service."""
    with streaming_data_measurement.measurement_service.host_service() as service:
        yield service
