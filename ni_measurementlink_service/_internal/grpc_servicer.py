"""gRPC servicers for each version of the measurement service interface."""

from __future__ import annotations

import collections.abc
import contextlib
import inspect
import pathlib
import weakref
from contextvars import ContextVar
from typing import Any, Callable, Dict, Generator, List, Optional

import grpc
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.parameter import serializer
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
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
    """Accessor for the measurement service's context-local state."""

    def __init__(
        self,
        grpc_context: grpc.ServicerContext,
        pin_map_context: PinMapContext,
        owner: Optional[weakref.ReferenceType[object]],
    ) -> None:
        """Initialize the measurement service context."""
        self._grpc_context = grpc_context
        self._pin_map_context = pin_map_context
        self._is_complete = False
        self._owner = owner

    def mark_complete(self) -> None:
        """Mark the current RPC as complete."""
        self._is_complete = True

    @property
    def grpc_context(self) -> grpc.ServicerContext:
        """Get the context for the RPC."""
        return self._grpc_context

    @property
    def owner(self) -> object:
        """The owner of the server (e.g. measurement service)."""
        if self._owner is None:
            return None
        return self._owner()  # dereference weak ref

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
        try:
            self._grpc_context.abort(code, details)
        except Exception as e:
            # If gRPC raises an empty exception, replace it with an RpcError.
            # This allows our logging interceptors to query the code/details.
            if type(e) is Exception:
                raise CustomRpcError(code, details) from e
            raise


class CustomRpcError(grpc.RpcError):
    """A custom exception class for handling gRPC RPC errors.

    gRPC's built-in RpcError is not directly configurable in Python, so this class
    enables the creation of custom RPC errors with specific error codes.
    """

    def __init__(self, code: grpc.StatusCode, details: str) -> None:
        """Initialize a CustomRpcError instance."""
        self._code = code
        self._details = details

    def code(self) -> grpc.StatusCode:
        """Get the gRPC status code."""
        return self._code

    def details(self) -> str:
        """Get the gRPC status details."""
        return self._details


measurement_service_context: ContextVar[MeasurementServiceContext] = ContextVar(
    "measurement_service_context"
)


def _get_mapping_by_parameter_name(
    mapping_by_id: Dict[int, Any], measure_function: Callable[[], None]
) -> Dict[str, Any]:
    """Transform a mapping by id into a mapping by parameter name (i.e. kwargs)."""
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


def _frame_metadata_dict(
    parameter_list: List[ParameterMetadata],
) -> Dict[int, ParameterMetadata]:
    metadata_dict = {}
    for i, parameter in enumerate(parameter_list, start=1):
        metadata_dict[i] = parameter
    return metadata_dict


class MeasurementServiceServicerV1(v1_measurement_service_pb2_grpc.MeasurementServiceServicer):
    """Measurement v1 servicer."""

    def __init__(
        self,
        measurement_info: MeasurementInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
        owner: object,
    ) -> None:
        """Initialize the measurement v1 servicer."""
        super().__init__()
        self._configuration_metadata = _frame_metadata_dict(configuration_parameter_list)
        self._output_metadata = _frame_metadata_dict(output_parameter_list)
        self._measurement_info = measurement_info
        self._measure_function = measure_function
        self._owner = weakref.ref(owner) if owner is not None else None  # avoid reference cycle

    def GetMetadata(  # noqa: N802 - function name should be lowercase
        self, request: v1_measurement_service_pb2.GetMetadataRequest, context: grpc.ServicerContext
    ) -> v1_measurement_service_pb2.GetMetadataResponse:
        """RPC API to get measurement metadata."""
        measurement_details = v1_measurement_service_pb2.MeasurementDetails(
            display_name=self._measurement_info.display_name, version=self._measurement_info.version
        )

        measurement_signature = v1_measurement_service_pb2.MeasurementSignature(
            configuration_parameters_message_type="ni.measurementlink.measurement.v1.MeasurementConfigurations",
            outputs_message_type="ni.measurementlink.measurement.v1.MeasurementOutputs",
        )

        for field_number, configuration_metadata in self._configuration_metadata.items():
            configuration_parameter = v1_measurement_service_pb2.ConfigurationParameter(
                field_number=field_number,
                name=configuration_metadata.display_name,
                repeated=configuration_metadata.repeated,
                type=configuration_metadata.type,
                annotations=configuration_metadata.annotations,
            )
            measurement_signature.configuration_parameters.append(configuration_parameter)

        measurement_signature.configuration_defaults.value = serializer.serialize_default_values(
            self._configuration_metadata
        )

        for field_number, output_metadata in self._output_metadata.items():
            output_parameter = v1_measurement_service_pb2.Output(
                field_number=field_number,
                name=output_metadata.display_name,
                type=output_metadata.type,
                repeated=output_metadata.repeated,
            )
            measurement_signature.outputs.append(output_parameter)

        metadata_response = v1_measurement_service_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_signature=measurement_signature,
            user_interface_details=None,
        )

        for ui_file_path in self._measurement_info.ui_file_paths:
            ui_details = v1_measurement_service_pb2.UserInterfaceDetails(
                file_url=pathlib.Path(ui_file_path).as_uri()
            )
            metadata_response.user_interface_details.append(ui_details)

        return metadata_response

    def Measure(  # noqa: N802 - function name should be lowercase
        self, request: v1_measurement_service_pb2.MeasureRequest, context: grpc.ServicerContext
    ) -> v1_measurement_service_pb2.MeasureResponse:
        """RPC API that executes the registered measurement method."""
        mapping_by_id = serializer.deserialize_parameters(
            self._configuration_metadata, request.configuration_parameters.value
        )
        mapping_by_variable_name = _get_mapping_by_parameter_name(
            mapping_by_id, self._measure_function
        )
        pin_map_context = PinMapContext._from_grpc(request.pin_map_context)
        token = measurement_service_context.set(
            MeasurementServiceContext(context, pin_map_context, self._owner)
        )
        try:
            return_value = self._measure_function(**mapping_by_variable_name)
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
            outputs=_serialize_outputs(self._output_metadata, outputs)
        )


class MeasurementServiceServicerV2(v2_measurement_service_pb2_grpc.MeasurementServiceServicer):
    """Measurement v2 servicer."""

    def __init__(
        self,
        measurement_info: MeasurementInfo,
        configuration_parameter_list: List[ParameterMetadata],
        output_parameter_list: List[ParameterMetadata],
        measure_function: Callable,
        owner: object,
    ) -> None:
        """Initialize the measurement v2 servicer."""
        super().__init__()
        self._configuration_metadata = _frame_metadata_dict(configuration_parameter_list)
        self._output_metadata = _frame_metadata_dict(output_parameter_list)
        self._measurement_info = measurement_info
        self._measure_function = measure_function
        self._owner = weakref.ref(owner) if owner is not None else None  # avoid reference cycle

    def GetMetadata(  # noqa: N802 - function name should be lowercase
        self, request: v2_measurement_service_pb2.GetMetadataRequest, context: grpc.ServicerContext
    ) -> v2_measurement_service_pb2.GetMetadataResponse:
        """RPC API to get measurement metadata."""
        measurement_details = v2_measurement_service_pb2.MeasurementDetails(
            display_name=self._measurement_info.display_name, version=self._measurement_info.version
        )

        measurement_signature = v2_measurement_service_pb2.MeasurementSignature(
            configuration_parameters_message_type="ni.measurementlink.measurement.v2.MeasurementConfigurations",
            outputs_message_type="ni.measurementlink.measurement.v2.MeasurementOutputs",
        )

        for field_number, configuration_metadata in self._configuration_metadata.items():
            configuration_parameter = v2_measurement_service_pb2.ConfigurationParameter(
                field_number=field_number,
                name=configuration_metadata.display_name,
                repeated=configuration_metadata.repeated,
                type=configuration_metadata.type,
                annotations=configuration_metadata.annotations,
                message_type=configuration_metadata.message_type,
            )
            measurement_signature.configuration_parameters.append(configuration_parameter)

        measurement_signature.configuration_defaults.value = serializer.serialize_default_values(
            self._configuration_metadata
        )

        for field_number, output_metadata in self._output_metadata.items():
            output_parameter = v2_measurement_service_pb2.Output(
                field_number=field_number,
                name=output_metadata.display_name,
                type=output_metadata.type,
                repeated=output_metadata.repeated,
                annotations=output_metadata.annotations,
                message_type=output_metadata.message_type,
            )
            measurement_signature.outputs.append(output_parameter)

        metadata_response = v2_measurement_service_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_signature=measurement_signature,
            user_interface_details=None,
        )

        for ui_file_path in self._measurement_info.ui_file_paths:
            ui_details = v2_measurement_service_pb2.UserInterfaceDetails(
                file_url=pathlib.Path(ui_file_path).as_uri()
            )
            metadata_response.user_interface_details.append(ui_details)

        return metadata_response

    def Measure(  # noqa: N802 - function name should be lowercase
        self, request: v2_measurement_service_pb2.MeasureRequest, context: grpc.ServicerContext
    ) -> Generator[v2_measurement_service_pb2.MeasureResponse, None, None]:
        """RPC API that executes the registered measurement method."""
        mapping_by_id = serializer.deserialize_parameters(
            self._configuration_metadata, request.configuration_parameters.value
        )
        mapping_by_variable_name = _get_mapping_by_parameter_name(
            mapping_by_id, self._measure_function
        )
        pin_map_context = PinMapContext._from_grpc(request.pin_map_context)
        token = measurement_service_context.set(
            MeasurementServiceContext(context, pin_map_context, self._owner)
        )
        try:
            return_value = self._measure_function(**mapping_by_variable_name)
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
            outputs=_serialize_outputs(self._output_metadata, outputs)
        )
