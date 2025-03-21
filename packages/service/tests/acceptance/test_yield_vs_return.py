"""Tests to validate that yield and return are both supported in v2 measurements."""

from collections.abc import Generator

import pytest
from google.protobuf import any_pb2

from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from tests.utilities.measurements import yield_vs_return_measurement
from tests.utilities.stubs.yieldvsreturn.types_pb2 import Configurations, Outputs


def test___measurement_utilizing_yield_and_return___call_measurement___receives_responses_from_yield_and_return(
    stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub,
):
    metadata = stub_v2.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    request = v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=_get_configuration_parameters(
            message_type=metadata.measurement_signature.configuration_parameters_message_type
        )
    )

    response_iterator = stub_v2.Measure(request)
    responses = [response for response in response_iterator]

    for index, response in enumerate(responses):
        output = Outputs()
        output.ParseFromString(response.outputs.value)
        if index + 1 == len(responses):
            assert output.status == f"Total updates: {index + 1}"
        else:
            assert output.status == f"Update: {index + 1}"


def _get_configuration_parameters(*args, message_type: str = "", **kwargs) -> any_pb2.Any:
    serialized_parameter = _get_serialized_measurement_configuration_parameters(*args, **kwargs)
    config_params_any = any_pb2.Any()
    config_params_any.type_url = "type.googleapis.com/" + message_type
    config_params_any.value = serialized_parameter
    return config_params_any


def _get_serialized_measurement_configuration_parameters(
    time_in_seconds: float = 1.0,
) -> bytes:
    config_params = Configurations(time_in_seconds=time_in_seconds)

    temp_any = any_pb2.Any()
    temp_any.Pack(config_params)
    grpc_serialized_data = temp_any.value
    return grpc_serialized_data


@pytest.fixture(scope="module")
def measurement_service(discovery_service_process) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with yield_vs_return_measurement.measurement_service.host_service() as service:
        yield service
