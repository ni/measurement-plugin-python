"""Python measurement client."""

from functools import cached_property
from typing import Any, Dict, List, NamedTuple, Tuple

import grpc
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.parameter.serializer import (
    deserialize_parameters,
    serialize_parameters,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurementlink_service.discovery import DiscoveryClient
from ni_measurementlink_service.pin_map import PinMapClient
from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2

_SITES = [0]
_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
_pin_map_path = ""

class _MeasurementClient:

    def __init__(self, service_class: str):
        self._service_class = service_class
        self._discovery_client = DiscoveryClient()
        self._configuration_metadata_by_id = {1: ParameterMetadata(display_name='pin_name', type=9, repeated=False, default_value='Pin1', annotations={'ni/ioresource.instrument_type': 'niDAQmx', 'ni/type_specialization': 'ioresource'}, message_type=''), 2: ParameterMetadata(display_name='sample_rate', type=1, repeated=False, default_value=1000.0, annotations={}, message_type=''), 3: ParameterMetadata(display_name='number_of_samples', type=4, repeated=False, default_value=60000, annotations={}, message_type='')}
        self._output_metadata_by_id = {1: ParameterMetadata(display_name='acquired_samples', type=1, repeated=True, default_value=0, annotations={}, message_type='')}

    @cached_property
    def _measurement_service_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        try:
            resolved_service = self._discovery_client.resolve_service(
                _V2_MEASUREMENT_SERVICE_INTERFACE, self._service_class
            )
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise RuntimeError(
                    "Failed to connect to the measurement service. Ensure if the measurement is running."
                )
            raise

        channel = grpc.insecure_channel(resolved_service.insecure_address)
        return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


    def _get_measure_request(self, args: Any) -> v2_measurement_service_pb2.MeasureRequest:
        serialized_configuration = any_pb2.Any(
            value=serialize_parameters(self._configuration_metadata_by_id, list(args))
        )
        return v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration,
            pin_map_context=PinMapContext(
                pin_map_id=_pin_map_path,
                sites=_SITES,
            ),
        )


    def _parse_enum_values_if_any(
        self, output_values: Dict[int, Any]
    ) -> Dict[int, Any]:
        for key, metadata in self._output_metadata_by_id.items():
            if metadata.annotations and metadata.annotations["ni/type_specialization"] == "enum":
                enum_type = type(eval(metadata.default_value))
                if metadata.repeated:
                    enum_values = []
                    for value in output_values[key]:
                        enum_values.append(enum_type(int(value)))
                    output_values[key] = enum_values
                else:
                    output_values[key] = enum_type(int(output_values[key]))
        return output_values


    def _measure(self, *args: Any) -> Tuple[Any]:
        request = self._get_measure_request(args)
        result = [None] * max(self._output_metadata_by_id.keys())
        for response in self._measurement_service_stub.Measure(request):
            output_values = deserialize_parameters(
                self._output_metadata_by_id, response.outputs.value
            )
            output_values = self._parse_enum_values_if_any(output_values)
            for k, v in output_values.items():
                result[k - 1] = v

        return tuple(result)


class Output(NamedTuple):
    """Measurement result container."""

    acquired_samples: List[float]


def measure(
    pin_name: str = "Pin1",
    sample_rate: float = 1000.0,
    number_of_samples: int = 60000
) -> Output:
    """MeasurementLink example that performs a finite analog input measurement with NI-DAQmx.

    Returns:
        Measurement output.
    """

    client = _MeasurementClient("ni.examples.NIDAQmxAnalogInput_Python")
    response = client._measure(
        pin_name,
        sample_rate,
        number_of_samples
    )
    return Output._make(response)


def register_pin_map(pin_map_absolute_path: str) -> str:
    """Registers the pin map with the pin map service.

    Args:
        pin_map_absolute_path: Absolute path of the pin map.

    Returns:
        Pin map id.
    """

    pin_map_client = PinMapClient()
    global _pin_map_path
    _pin_map_path = pin_map_absolute_path

    return pin_map_client.update_pin_map(_pin_map_path)
