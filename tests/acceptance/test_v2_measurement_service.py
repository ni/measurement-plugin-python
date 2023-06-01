"""Tests to validate a v2 measurement service that streams data."""
from typing import Generator, List

import grpc
import pytest
from examples.sample_streaming_measurement import measurement
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.service import MeasurementService
from tests.assets import sample_streaming_measurement_test_pb2


@pytest.mark.parametrize("num_responses", [1, 10, 100])
def test___streaming_measurement_service___request_number_of_responses___receives_responses(
    num_responses: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    """End to End Test validating streaming measurement returns the expected number of responses."""
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(num_responses=num_responses)
    )

    response_iterator = stub_v2.Measure(request)
    responses = [response for response in response_iterator]


@pytest.mark.parametrize("data_size", [1, 10, 100])
def test___streaming_measurement_service___request_data_cumulatively___receives_expected_amount_of_data(
    data_size: int, stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub
):
    """End to End Test validating measurement returns expected amount of cumulatively data."""
    name = "testing-cumulative"
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            name=name,
            data_size=data_size,
            cumulative_data=True,
        )
    )

    response_iterator = stub_v2.Measure(request)

    expected_data: List[int] = []
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
    """End to End Test validating measurement returns the expected amount of non-cumulative data."""
    name = "testing-not-cumulative"
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
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
    """End to End Test validating streaming measurement sends responses prior to expected error."""
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(error_on_index=error_on_index)
    )

    response_iterator = stub_v2.Measure(request)

    index = 0
    with pytest.raises(grpc.RpcError):
        for response in response_iterator:
            index += 1

    assert index == error_on_index


def _get_configuration_parameters(*args, **kwargs) -> any_pb2.Any:
    serialized_parameter = _get_serialized_measurement_configuration_parameters(*args, **kwargs)
    config_params_any = any_pb2.Any()
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
    config_params = sample_streaming_measurement_test_pb2.SampleStreamingMeasurementParameter()
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
    data: List[int],
) -> bytes:
    config_params = sample_streaming_measurement_test_pb2.SampleStreamingMeasurementOutput()
    config_params.name = name
    config_params.index = index
    config_params.data.extend(data)

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


@pytest.fixture(scope="module")
def measurement_service() -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with measurement.measurement_service.host_service() as service:
        yield service
