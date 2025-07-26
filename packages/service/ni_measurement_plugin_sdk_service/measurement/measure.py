from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable

from google.protobuf import any_pb2, timestamp_pb2
from ni.datamonikers.v1 import MonikerClient, data_moniker_pb2
from ni.measurements.data.v1 import DataStoreClient, data_store_pb2
from ni.measurementlink.measurement.v3 import (
    measurement_service_pb2 as v3_measurement_service_pb2,
)

from ni_measurement_plugin_sdk_service.measurement.info import (
    DataType,
    MonikerType,
    ParameterType,
)


class MeasureRequest:
    def __init__(
        self,
        moniker_client: MonikerClient,
        inputs: dict[str, ParameterType],
        grpc_request: v3_measurement_service_pb2.MeasureRequest,
    ):
        self._moniker_client = moniker_client
        self._inputs = inputs
        self._grpc_request = grpc_request

        self._input_positions = {key: i for i, key in enumerate(inputs.keys())}

    def __getattr__(self, input_name: str) -> Awaitable:
        suffix = "_moniker"
        true_input_name = input_name.removesuffix(suffix)
        has_moniker_suffix = true_input_name != input_name

        parameter_type = self._inputs[true_input_name]
        position = self._input_positions[true_input_name]

        if isinstance(parameter_type, MonikerType):
            moniker = self._grpc_request.inputs[position].moniker
            if has_moniker_suffix:
                return moniker
            else:
                return self.__convert_from_moniker(parameter_type, moniker)
        elif isinstance(parameter_type, DataType):
            data = self._grpc_request.inputs[position].value
            return self.__convert_from_value(parameter_type, data)
        else:
            raise ValueError(f"Unsupported parameter type: {parameter_type}")

    async def __convert_from_moniker(
        self, parameter_type: MonikerType, moniker: data_moniker_pb2.Moniker
    ):
        result = await self._moniker_client.read_from_moniker(moniker)
        if result.type_url != parameter_type.to_url():
            raise ValueError(
                f"Moniker type {result.value.type_url} does not match expected type {parameter_type.to_url()}"
            )

        value = parameter_type.to_message()
        result.Unpack(value)
        return value

    async def __convert_from_value(self, parameter_type: DataType, data: any_pb2.Any):
        if data.type_url != parameter_type.to_url():
            raise ValueError(
                f"Value type {data.type_url} does not match expected type {parameter_type.to_url()}"
            )

        value = parameter_type.to_message()
        data.Unpack(value)
        return value


@dataclass(frozen=True, init=False)
class MeasureOutput:
    measurement_id: str
    name: str
    value: Any
    data_name: str | None = None

    def __init__(
        self,
        measurement_id: str,
        *,
        data_name: str = None,
        **output,
    ):
        """
        Initialize MeasureOutput with optional metadata and required output parameters.

        Args:
            measurement_id: Required id for an existing measurement
            data_name: Optional name for the published data
            **output: Required named output parameter (e.g., voltage=5.0)

        Raises:
            ValueError: If no output parameters are provided
        """
        if not output:
            raise ValueError("An output parameter must be provided")

        object.__setattr__(self, "measurement_id", measurement_id)
        object.__setattr__(self, "name", list(output.keys())[0])
        object.__setattr__(self, "value", list(output.values())[0])
        object.__setattr__(self, "data_name", data_name)


class MeasureResponse:
    def __init__(self, *measure_outputs: MeasureOutput):
        """
        Initialize MeasureResponse with multiple MeasureOutput instances.

        Args:
            *measure_outputs: Variable number of MeasureOutput instances

        Raises:
            ValueError: If no MeasureOutput instances are provided
            TypeError: If any argument is not a MeasureOutput instance
        """
        if not measure_outputs:
            raise ValueError("At least one MeasureOutput must be provided")

        for output in measure_outputs:
            if not isinstance(output, MeasureOutput):
                raise TypeError(f"Expected MeasureOutput, got {type(output)}")

        self._measure_outputs = measure_outputs

    async def to_grpc_response(
        self, ds_client: DataStoreClient, output_parameters: dict[str, ParameterType]
    ) -> v3_measurement_service_pb2.MeasureResponse:
        """Convert this MeasureResponse to a gRPC MeasureResponse."""
        data_values = []

        for parameter_name, parameter_type in output_parameters.items():
            if parameter_name not in [output.name for output in self._measure_outputs]:
                raise ValueError(f"Output '{parameter_name}' not found in MeasureOutputs")

            measure_output = next(
                output for output in self._measure_outputs if output.name == parameter_name
            )
            if isinstance(parameter_type, MonikerType):
                publishable_data = data_store_pb2.PublishableData(name=measure_output.data_name)
                if parameter_type == MonikerType.ScalarData:
                    publishable_data.scalar_data.CopyFrom(measure_output.value)
                elif (
                    parameter_type == MonikerType.ScalarArray
                    or parameter_type == MonikerType.String2DArray
                    or parameter_type == MonikerType.Double2DArray
                ):
                    publishable_data.scalar_array.CopyFrom(measure_output.value)
                elif parameter_type == MonikerType.ConditionSet:
                    ...
                elif parameter_type == MonikerType.DoubleXYData:
                    publishable_data.x_y_data.CopyFrom(measure_output.value)
                elif parameter_type == MonikerType.DoubleAnalogWaveform:
                    publishable_data.waveform.CopyFrom(measure_output.value)
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(datetime.now(timezone.utc))
                result = await ds_client.publish_data(
                    publishable_data,
                    data_store_pb2.PublishDataLocation.PUBLISH_DATA_LOCATION_LOCAL,
                    timestamp,
                    measure_output.measurement_id,
                )
                data_values.append(v3_measurement_service_pb2.DataValue(moniker=result.moniker))
            else:
                value = parameter_type.to_message(measure_output.value)
                any_value = any_pb2.Any()
                any_value.Pack(value)
                data_values.append(v3_measurement_service_pb2.DataValue(value=any_value))

        return v3_measurement_service_pb2.MeasureResponse(outputs=data_values)
