"""Contains Measurement Service Implementation class and method to host the service.
"""
import collections.abc
import contextlib
import inspect
import pathlib
from contextvars import ContextVar
from typing import Any, Callable, Dict, Generator, List

import grpc
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.parameter import serializer
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.stubs.ni.measurementlink import (
    pin_map_context_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2 as v1_measurement_service_pb2,
    measurement_service_pb2_grpc as v1_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.info import MeasurementInfo
from ni_measurementlink_service.session_management import PinMapContext


class MeasurementServiceContext:
    """Accessor for the Measurement Service's context-local state."""

    def __init__(
        self,
        grpc_context: grpc.ServicerContext,
        pin_map_context: PinMapContext,
    ) -> None:
        """Initialize the Measurement Service Context."""
        self._grpc_context: grpc.ServicerContext = grpc_context
        self._pin_map_context: PinMapContext = pin_map_context
        self._is_complete: bool = False

    def mark_complete(self) -> None:
        """Mark the current RPC as complete."""
        self._is_complete = True

    @property
    def grpc_context(self) -> grpc.ServicerContext:
        """Get the context for the RPC."""
        return self._grpc_context

    @property
    def pin_map_context(self) -> PinMapContext:
        """Get the pin map context for the RPC."""
        return self._pin_map_context

    def add_cancel_callback(self, cancel_callback: Callable[[], None]) -> None:
        """Add a callback that is invoked when the RPC is canceled."""

        def grpc_callback() -> None:
            if not self._is_complete:
                cancel_callback()

        self._grpc_context.add_callback(grpc_callback)

    def cancel(self) -> None:
        """Cancel the RPC."""
        if not self._is_complete:
            self._grpc_context.cancel()

    @property
    def time_remaining(self) -> float:
        """Get the time remaining for the RPC."""
        return self._grpc_context.time_remaining()

    def abort(self, code: grpc.StatusCode, details: str) -> None:
        """Aborts the RPC."""
        self._grpc_context.abort(code, details)


measurement_service_context: ContextVar[MeasurementServiceContext] = ContextVar(
    "measurement_service_context"
)


def _convert_pin_map_context_from_grpc(
    grpc_pin_map_context: pin_map_context_pb2.PinMapContext,
) -> PinMapContext:
    # The protobuf PinMapContext sites field is a RepeatedScalarContainer, not a list.
    # Constructing a protobuf PinMapContext with sites=None sets sites to an empty
    # RepeatedScalarContainer, not None.
    return PinMapContext(
        pin_map_id=grpc_pin_map_context.pin_map_id,
        sites=list(grpc_pin_map_context.sites),
    )


def _get_mapping_by_parameter_name(
    mapping_by_id: Dict[int, Any], measure_function: Callable[[], None]
) -> Dict[str, Any]:
    """Transform the mapping by id to mapping by parameter names of the measurement function.

    Args
    ----
        mapping_by_id (Dict[int, Any]): Mapping by ID

        measure_function (callable): Function from which the parameter names are extracted.

    Returns
    -------
        Dict[str, Any]: Mapping by Parameters names based on the measurement function.

    """
    signature = inspect.signature(measure_function)
    mapping_by_variable_name = {}
    for i, parameter in enumerate(signature.parameters.values(), start=1):
        mapping_by_variable_name[parameter.name] = mapping_by_id[i]
    return mapping_by_variable_name


def _serialize_outputs(output_metadata: Dict[int, ParameterMetadata], outputs: Any) -> any_pb2.Any:
    if isinstance(outputs, collections.abc.Sequence):
        return any_pb2.Any(value=serializer.serialize_parameters(output_metadata, outputs))
    elif outputs is None:
        raise ValueError(f"Measurement function returned None")
    else:
        raise TypeError(
            f"Measurement function returned value with unsupported type: {type(outputs)}"
        )


class MeasurementServiceServicerV1(v1_measurement_service_pb2_grpc.MeasurementServiceServicer):
    """Implementation of the Measurement Service's gRPC base class.

    Attributes
    ----------
        measurement_info (MeasurementInfo): Measurement info

        configuration_parameter_list (List): List of configuration parameters.

        output_parameter_list (List): List of output parameters.

        measure_function (Callable): Registered measurement function.

    """

    def __init__(
        self,
        measurement_info: MeasurementInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
    ) -> None:
        """Initialize the Measurement Service Servicer.

        Args:
            measurement_info (MeasurementInfo): Measurement info

            configuration_parameter_list (List): List of configuration parameters.

            output_parameter_list (List): List of output parameters.

            measure_function (Callable): Registered measurement function.

        """
        super().__init__()

        def frame_metadata_dict(
            parameter_list: List[ParameterMetadata],
        ) -> Dict[int, ParameterMetadata]:
            metadata_dict = {}
            for i, parameter in enumerate(parameter_list, start=1):
                metadata_dict[i] = parameter
            return metadata_dict

        self.configuration_metadata: Dict[int, ParameterMetadata] = frame_metadata_dict(
            configuration_parameter_list
        )
        self.output_metadata: Dict[int, ParameterMetadata] = frame_metadata_dict(
            output_parameter_list
        )
        self.measurement_info: MeasurementInfo = measurement_info
        self.measure_function = measure_function

    def GetMetadata(  # noqa: N802 - function name should be lowercase
        self, request: v1_measurement_service_pb2.GetMetadataRequest, context: grpc.ServicerContext
    ) -> v1_measurement_service_pb2.GetMetadataResponse:
        """RPC API to get complete metadata."""
        # measurement details
        measurement_details = v1_measurement_service_pb2.MeasurementDetails()
        measurement_details.display_name = self.measurement_info.display_name
        measurement_details.version = self.measurement_info.version

        # Measurement Parameters
        measurement_signature = v1_measurement_service_pb2.MeasurementSignature(
            configuration_parameters_message_type="ni.measurementlink.measurement.v1.MeasurementConfigurations",
            outputs_message_type="ni.measurementlink.measurement.v1.MeasurementOutputs",
        )

        # Configurations
        for field_number, configuration_metadata in self.configuration_metadata.items():
            configuration_parameter = v1_measurement_service_pb2.ConfigurationParameter()
            configuration_parameter.field_number = field_number
            configuration_parameter.name = configuration_metadata.display_name
            configuration_parameter.repeated = configuration_metadata.repeated
            configuration_parameter.type = configuration_metadata.type
            configuration_parameter.annotations.update(configuration_metadata.annotations)
            measurement_signature.configuration_parameters.append(configuration_parameter)

        # Configuration Defaults
        measurement_signature.configuration_defaults.value = serializer.serialize_default_values(
            self.configuration_metadata
        )

        # Output Parameters Metadata
        for field_number, output_metadata in self.output_metadata.items():
            output_parameter = v1_measurement_service_pb2.Output()
            output_parameter.field_number = field_number
            output_parameter.name = output_metadata.display_name
            output_parameter.type = output_metadata.type
            output_parameter.repeated = output_metadata.repeated
            measurement_signature.outputs.append(output_parameter)

        # Sending back Response
        metadata_response = v1_measurement_service_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_signature=measurement_signature,
            user_interface_details=None,
        )

        # User Interface details - Framed relative to the metadata python File
        for ui_file_path in self.measurement_info.ui_file_paths:
            ui_details = v1_measurement_service_pb2.UserInterfaceDetails()
            ui_details.file_url = pathlib.Path(ui_file_path).as_uri()
            metadata_response.user_interface_details.append(ui_details)

        return metadata_response

    def Measure(  # noqa: N802 - function name should be lowercase
        self, request: v1_measurement_service_pb2.MeasureRequest, context: grpc.ServicerContext
    ) -> v1_measurement_service_pb2.MeasureResponse:
        """RPC API that Executes the registered measurement method."""
        mapping_by_id = serializer.deserialize_parameters(
            self.configuration_metadata, request.configuration_parameters.value
        )

        # Calling the registered measurement
        mapping_by_variable_name = _get_mapping_by_parameter_name(
            mapping_by_id, self.measure_function
        )
        pin_map_context = _convert_pin_map_context_from_grpc(request.pin_map_context)
        token = measurement_service_context.set(MeasurementServiceContext(context, pin_map_context))
        try:
            return_value = self.measure_function(**mapping_by_variable_name)
            if isinstance(return_value, collections.abc.Generator):
                with contextlib.closing(return_value) as output_iter:
                    outputs = None
                    try:
                        while True:
                            outputs = next(output_iter)
                    except StopIteration as e:
                        if e.value is not None:
                            outputs = e.value
                    return self._serialize_response(outputs)
            else:
                return self._serialize_response(return_value)
        finally:
            measurement_service_context.get().mark_complete()
            measurement_service_context.reset(token)

    def _serialize_response(self, outputs: Any) -> v1_measurement_service_pb2.MeasureResponse:
        return v1_measurement_service_pb2.MeasureResponse(
            outputs=_serialize_outputs(self.output_metadata, outputs)
        )


class MeasurementServiceServicerV2(v2_measurement_service_pb2_grpc.MeasurementServiceServicer):
    """Implementation of the Measurement Service's gRPC base class.

    Attributes
    ----------
        measurement_info (MeasurementInfo): Measurement info

        configuration_parameter_list (List): List of configuration parameters.

        output_parameter_list (List): List of output parameters.

        measure_function (Callable): Registered measurement function.

    """

    def __init__(
        self,
        measurement_info: MeasurementInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
    ) -> None:
        """Initialize the Measurement Service Servicer.

        Args:
            measurement_info (MeasurementInfo): Measurement info

            configuration_parameter_list (List): List of configuration parameters.

            output_parameter_list (List): List of output parameters.

            measure_function (Callable): Registered measurement function.

        """
        super().__init__()

        def frame_metadata_dict(
            parameter_list: List[ParameterMetadata],
        ) -> Dict[int, ParameterMetadata]:
            metadata_dict = {}
            for i, parameter in enumerate(parameter_list, start=1):
                metadata_dict[i] = parameter
            return metadata_dict

        self.configuration_metadata: Dict[int, ParameterMetadata] = frame_metadata_dict(
            configuration_parameter_list
        )
        self.output_metadata: Dict[int, ParameterMetadata] = frame_metadata_dict(
            output_parameter_list
        )
        self.measurement_info: MeasurementInfo = measurement_info
        self.measure_function = measure_function

    def GetMetadata(  # noqa: N802 - function name should be lowercase
        self, request: v2_measurement_service_pb2.GetMetadataRequest, context: grpc.ServicerContext
    ) -> v2_measurement_service_pb2.GetMetadataResponse:
        """RPC API to get complete metadata."""
        # measurement details
        measurement_details = v2_measurement_service_pb2.MeasurementDetails()
        measurement_details.display_name = self.measurement_info.display_name
        measurement_details.version = self.measurement_info.version

        # Measurement Parameters
        measurement_signature = v2_measurement_service_pb2.MeasurementSignature(
            configuration_parameters_message_type="ni.measurementlink.measurement.v2.MeasurementConfigurations",
            outputs_message_type="ni.measurementlink.measurement.v2.MeasurementOutputs",
        )

        # Configurations
        for field_number, configuration_metadata in self.configuration_metadata.items():
            configuration_parameter = v2_measurement_service_pb2.ConfigurationParameter()
            configuration_parameter.field_number = field_number
            configuration_parameter.name = configuration_metadata.display_name
            configuration_parameter.repeated = configuration_metadata.repeated
            configuration_parameter.type = configuration_metadata.type
            configuration_parameter.annotations.update(configuration_metadata.annotations)
            configuration_parameter.message_type = configuration_metadata.message_type
            measurement_signature.configuration_parameters.append(configuration_parameter)

        # Configuration Defaults
        measurement_signature.configuration_defaults.value = serializer.serialize_default_values(
            self.configuration_metadata
        )

        # Output Parameters Metadata
        for field_number, output_metadata in self.output_metadata.items():
            output_parameter = v2_measurement_service_pb2.Output()
            output_parameter.field_number = field_number
            output_parameter.name = output_metadata.display_name
            output_parameter.type = output_metadata.type
            output_parameter.repeated = output_metadata.repeated
            output_parameter.annotations.update(output_metadata.annotations)
            output_parameter.message_type = output_metadata.message_type
            measurement_signature.outputs.append(output_parameter)

        # Sending back Response
        metadata_response = v2_measurement_service_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_signature=measurement_signature,
            user_interface_details=None,
        )

        # User Interface details - Framed relative to the metadata python File
        for ui_file_path in self.measurement_info.ui_file_paths:
            ui_details = v2_measurement_service_pb2.UserInterfaceDetails()
            ui_details.file_url = pathlib.Path(ui_file_path).as_uri()
            metadata_response.user_interface_details.append(ui_details)

        return metadata_response

    def Measure(  # noqa: N802 - function name should be lowercase
        self, request: v2_measurement_service_pb2.MeasureRequest, context: grpc.ServicerContext
    ) -> Generator[v2_measurement_service_pb2.MeasureResponse, None, None]:
        """RPC API that Executes the registered measurement method."""
        mapping_by_id = serializer.deserialize_parameters(
            self.configuration_metadata, request.configuration_parameters.value
        )

        # Calling the registered measurement
        mapping_by_variable_name = _get_mapping_by_parameter_name(
            mapping_by_id, self.measure_function
        )
        pin_map_context = _convert_pin_map_context_from_grpc(request.pin_map_context)
        token = measurement_service_context.set(MeasurementServiceContext(context, pin_map_context))
        try:
            return_value = self.measure_function(**mapping_by_variable_name)
            if isinstance(return_value, collections.abc.Generator):
                with contextlib.closing(return_value) as output_iter:
                    try:
                        while True:
                            outputs = next(output_iter)
                            yield self._serialize_response(outputs)
                    except StopIteration as e:
                        if e.value is not None:
                            yield self._serialize_response(e.value)
            else:
                yield self._serialize_response(return_value)
        finally:
            measurement_service_context.get().mark_complete()
            measurement_service_context.reset(token)

    def _serialize_response(self, outputs: Any) -> v2_measurement_service_pb2.MeasureResponse:
        return v2_measurement_service_pb2.MeasureResponse(
            outputs=_serialize_outputs(self.output_metadata, outputs)
        )
