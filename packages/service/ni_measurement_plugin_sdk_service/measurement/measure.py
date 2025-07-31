from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable

from google.protobuf import any_pb2, timestamp_pb2
from google.protobuf.message import Message
from ni.datamonikers.v1 import MonikerClient, data_moniker_pb2
from ni.measurementlink.measurement.v3 import measurement_service_pb2 as v3_measurement_service_pb2
from ni.measurements.data.v1 import DataStoreClient, data_store_pb2
from ni.protobuf.types import array_pb2, scalar_pb2, waveform_pb2, xydata_pb2

from ni_measurement_plugin_sdk_service.measurement.info import DataType, MonikerType, ParameterType


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

    def __getattr__(self, input_name: str) -> Awaitable[Any] | data_moniker_pb2.Moniker:
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
    ) -> Message:
        result = await self._moniker_client.read_from_moniker(moniker)
        if result.type_url != parameter_type.to_url():
            raise ValueError(
                f"Moniker type {result.value.type_url} does not match expected type {parameter_type.to_url()}"
            )

        value = parameter_type.to_message()
        result.Unpack(value)
        return value

    async def __convert_from_value(self, parameter_type: DataType, data: any_pb2.Any) -> Message:
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
                publishable_data = self.__to_publishable_data(
                    parameter_name, parameter_type, measure_output
                )
                timestamp = timestamp_pb2.Timestamp()
                timestamp.FromDatetime(datetime.now(timezone.utc))
                result = await ds_client.publish_data(
                    publishable_data,
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

    def __to_publishable_data(
        self, parameter_name: str, parameter_type: MonikerType, output: MeasureOutput
    ) -> data_store_pb2.PublishableData:
        """Convert MeasureOutput to PublishableData."""
        if output.data_name is None:
            raise ValueError(f"Output '{parameter_name}' must have a value for data_name")

        publishable_data = data_store_pb2.PublishableData(name=output.data_name)
        if parameter_type == MonikerType.Scalar:
            if isinstance(output.value, scalar_pb2.Scalar):
                scalar = output.value
            else:
                scalar = scalar_pb2.Scalar()
                if isinstance(output.value, float):
                    scalar.double_value = output.value
                elif isinstance(output.value, int):
                    scalar.int_value = output.value
                elif isinstance(output.value, bool):
                    scalar.bool_value = output.value
                elif isinstance(output.value, str):
                    scalar.string_value = output.value

            publishable_data.scalar.CopyFrom(scalar)
        elif parameter_type == MonikerType.ScalarArray:
            if isinstance(output.value, data_store_pb2.ScalarArray):
                scalar_array = output.value
            else:
                scalar_array = data_store_pb2.ScalarArray()
                first_value = output.value[0]
                if isinstance(first_value, float):
                    scalar_array.double_array.values.extend(output.value)
                elif isinstance(first_value, int):
                    scalar_array.int32_array.values.extend(output.value)
                elif isinstance(first_value, bool):
                    scalar_array.bool_array.values.extend(output.value)
                elif isinstance(first_value, str):
                    scalar_array.string_array.values.extend(output.value)

            publishable_data.scalar_array.CopyFrom(scalar_array)
        elif parameter_type == MonikerType.String2DArray:
            scalar_array = data_store_pb2.ScalarArray()
            if isinstance(output.value, array_pb2.String2DArray):
                scalar_array.string_array.values.extend(output.value.data)
            else:
                if not isinstance(output.value, tuple[int, int, list[str]]):
                    raise ValueError(
                        f"Expected {parameter_name} to be either a String2DArray or a tuple of (rows, columns, values)"
                    )
                _, _, values = output.value
                scalar_array.string_array.values.extend(values)

            publishable_data.scalar_array.CopyFrom(scalar_array)
        elif parameter_type == MonikerType.Double2DArray:
            scalar_array = data_store_pb2.ScalarArray()
            if isinstance(output.value, array_pb2.Double2DArray):
                scalar_array.double_array.values.extend(output.value.data)
            else:
                if not isinstance(output.value, tuple[int, int, list[float]]):
                    raise ValueError(
                        f"Expected {parameter_name} to be either a Double2DArray or a tuple of (rows, columns, values)"
                    )
                _, _, values = output.value
                scalar_array.double_array.values.extend(values)

            publishable_data.scalar_array.CopyFrom(scalar_array)
        elif parameter_type == MonikerType.ConditionSet:
            # TODO: Publish condition set
            ...
        elif parameter_type == MonikerType.DoubleXYData:
            if isinstance(output.value, xydata_pb2.DoubleXYData):
                xy_data = output.value
            else:
                xy_data = xydata_pb2.DoubleXYData()
                if isinstance(output.value, tuple[list[float], list[float]]):
                    x_values, y_values = output.value
                    xy_data.x_data.extend(x_values)
                    xy_data.y_data.extend(y_values)
                else:
                    raise ValueError(
                        f"Expected {parameter_name} to be a DoubleXYData or a tuple of (x_values, y_values)"
                    )

            publishable_data.x_y_data.CopyFrom(xy_data)
        elif parameter_type == MonikerType.DoubleAnalogWaveform:
            if isinstance(output.value, waveform_pb2.DoubleAnalogWaveform):
                waveform = output.value
            else:
                # TODO
                raise NotImplementedError(f"Expected {parameter_name} to be a DoubleAnalogWaveform")

            publishable_data.waveform.CopyFrom(waveform)

        return publishable_data
