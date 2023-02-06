"""Contains Measurement Service Implementation class and method to host the service.
"""
import inspect
import pathlib
from contextvars import ContextVar
from typing import Any, Callable, Dict, List

import grpc
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.parameter import serializer
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.stubs.ni.measurementlink import (
    pin_map_context_pb2,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v1 import (
    measurement_service_pb2,
    measurement_service_pb2_grpc,
)
from ni_measurementlink_service.measurement.info import MeasurementInfo


class MeasurementServiceContext:
    """Accessor for the Measurement Service's context-local state."""

    def __init__(
        self, grpc_context: grpc.ServicerContext, pin_map_context: pin_map_context_pb2.PinMapContext
    ):
        """Initialize the Measurement Service Context."""
        self._grpc_context: grpc.ServicerContext = grpc_context
        self._pin_map_context: pin_map_context_pb2.PinMapContext = pin_map_context
        self._is_complete: bool = False

    def mark_complete(self):
        """Mark the current RPC as complete."""
        self._is_complete = True

    @property
    def grpc_context(self):
        """Get the context for the RPC."""
        return self._grpc_context

    @property
    def pin_map_context(self):
        """Get the pin map context for the RPC."""
        return self._pin_map_context

    def add_cancel_callback(self, cancel_callback: Callable):
        """Add a callback that is invoked when the RPC is canceled."""

        def grpc_callback():
            if not self._is_complete:
                cancel_callback()

        self._grpc_context.add_callback(grpc_callback)

    def cancel(self):
        """Cancel the RPC."""
        if not self._is_complete:
            self._grpc_context.cancel()

    @property
    def time_remaining(self):
        """Get the time remaining for the RPC."""
        return self._grpc_context.time_remaining()

    def abort(self, code, details):
        """Aborts the RPC."""
        self._grpc_context.abort(code, details)


measurement_service_context: ContextVar[MeasurementServiceContext] = ContextVar(
    "measurement_service_context"
)


class MeasurementServiceServicer(measurement_service_pb2_grpc.MeasurementServiceServicer):
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
        output_parameter_list: list,
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

        def frame_metadata_dict(parameter_list: list):
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

    def GetMetadata(self, request, context):  # noqa N802:inherited method names-autogen baseclass
        """RPC API to get complete metadata."""
        # measurement details
        measurement_details = measurement_service_pb2.MeasurementDetails()
        measurement_details.display_name = self.measurement_info.display_name
        measurement_details.version = self.measurement_info.version

        # Measurement Parameters
        measurement_signature = measurement_service_pb2.MeasurementSignature(
            configuration_parameters_message_type="ni.measurementlink.measurement.v1.MeasurementConfigurations",
            outputs_message_type="ni.measurementlink.measurement.v1.MeasurementOutputs",
        )

        # Configurations
        for field_number, configuration_metadata in self.configuration_metadata.items():
            configuration_parameter = measurement_service_pb2.ConfigurationParameter()
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
            output_parameter = measurement_service_pb2.Output()
            output_parameter.field_number = field_number
            output_parameter.name = output_metadata.display_name
            output_parameter.type = output_metadata.type
            output_parameter.repeated = output_metadata.repeated
            measurement_signature.outputs.append(output_parameter)

        # Sending back Response
        metadata_response = measurement_service_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_signature=measurement_signature,
            user_interface_details=None,
        )

        # User Interface details - Framed relative to the metadata python File
        for ui_file_path in self.measurement_info.ui_file_paths:
            ui_details = measurement_service_pb2.UserInterfaceDetails()
            ui_details.file_url = pathlib.Path(ui_file_path).as_uri()
            metadata_response.user_interface_details.append(ui_details)

        return metadata_response

    def Measure(self, request, context):  # noqa N802:inherited method names-autogen baseclass
        """RPC API that Executes the registered measurement method."""
        byte_string = request.configuration_parameters.value
        mapping_by_id = serializer.deserialize_parameters(self.configuration_metadata, byte_string)

        # Calling the registered measurement
        mapping_by_variable_name = self._get_mapping_by_parameter_name(
            mapping_by_id, self.measure_function
        )
        token = measurement_service_context.set(
            MeasurementServiceContext(context, request.pin_map_context)
        )
        try:
            output_value = self.measure_function(**mapping_by_variable_name)
        finally:
            measurement_service_context.get().mark_complete()
            measurement_service_context.reset(token)
        output_bytestring = serializer.serialize_parameters(self.output_metadata, output_value)
        # Frame the response and send back.
        output_any = any_pb2.Any()
        output_any.value = output_bytestring
        return_value = measurement_service_pb2.MeasureResponse(outputs=output_any)
        return return_value

    def _get_mapping_by_parameter_name(
        self, mapping_by_id: Dict[int, Any], measure_function: Callable[[], None]
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
