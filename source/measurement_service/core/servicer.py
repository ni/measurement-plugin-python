"""Internal Helper Measurement Services.

Not Edited by User.
"""


import inspect
import io
from concurrent import futures

import google.protobuf.any_pb2 as grpc_any
import grpc
from measurement_service.stubs import Measurement_pb2
from measurement_service.stubs import Measurement_pb2_grpc


from measurement_service.core.parameter import serializer
import measurement_service.core.parameter.metadata as parameter_metadata
import measurement_service.framework as framework


class MeasurementServiceServicer(Measurement_pb2_grpc.MeasurementServiceServicer):
    """Implementation of gRPC Service - MeasurementService."""

    def __init__(self, measurement_info, configuration_parameter_list, output_parameter_list, measure_function) -> None:
        super().__init__()

        def frame_metadata_dict(parameter_list: list):
            metadata_dict = {}
            for i, parameter in enumerate(parameter_list, start=1):
                metadata_dict[i] = parameter
            return metadata_dict

        self.configuration_metadata: dict = frame_metadata_dict(configuration_parameter_list)
        self.output_metadata: dict = frame_metadata_dict(output_parameter_list)
        self.measurement_info: framework.MeasurementInfo = measurement_info
        self.measure_function = measure_function

    def GetMetadata(self, request, context):  # noqa N802:inherited method names-autogen baseclass
        """RPC Method that Get the Metdata of a Measurement."""

        # measurement details
        measurement_details = Measurement_pb2.MeasurementDetails()
        measurement_details.display_name = self.measurement_info.display_name
        measurement_details.version = self.measurement_info.version
        measurement_details.measurement_type = self.measurement_info.measurement_type
        measurement_details.product_type = self.measurement_info.product_type

        # Measurement Parameters
        measurement_parameters = Measurement_pb2.MeasurementParameters(
            configuration_parameters_messagetype="ni.measurements.v1.MeasurementConfigurations",
            outputs_message_type="ni.measurements.v1.MeasurementOutputs",
        )

        # Configurations
        for id, configuration_metadata in self.configuration_metadata.items():
            configuration_metadata: parameter_metadata.ParameterMetadata
            configuration_parameter = Measurement_pb2.ConfigurationParameter()
            configuration_parameter.protobuf_id = id
            configuration_parameter.name = configuration_metadata.display_name
            configuration_parameter.repeated = configuration_metadata.repeated
            configuration_parameter.type = configuration_metadata.type
            measurement_parameters.configuration_parameters.append(configuration_parameter)

        # Output Parameters Metadata
        for id, output_metadata in self.output_metadata.items():
            output_metadata: parameter_metadata.ParameterMetadata
            output_parameter = Measurement_pb2.Output()
            output_parameter.protobuf_id = id
            output_parameter.name = output_metadata.display_name
            output_parameter.type = output_metadata.type
            output_parameter.repeated = output_metadata.repeated
            measurement_parameters.outputs.append(output_parameter)

        # User Interface details - Framed relative to the metadata python File
        ui_details = Measurement_pb2.UserInterfaceDetails()

        ui_details.configuration_ui_url = self.measurement_info.ui_file_type + "\\" + self.measurement_info.ui_file_path

        # Sending back Response
        metadata_response = Measurement_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_parameters=measurement_parameters,
            user_interface_details=ui_details,
        )
        return metadata_response

    def Measure(self, request, context):  # noqa N802:inherited method names-autogen baseclass
        """RPC Method that Executes the Measurement."""
        byte_string = request.configuration_parameters.value
        byte_io = io.BytesIO()
        byte_io.write(byte_string)
        mapping_by_id = serializer.deserialize_parameters(self.configuration_metadata, byte_io.getbuffer())
        signature = inspect.signature(self.measure_function)
        # Calling the registered measurement
        mapping_by_variable_name = {}
        for i, parameter in enumerate(signature.parameters.values(), start=1):
            mapping_by_variable_name[parameter.name] = mapping_by_id[i]
        output_value = self.measure_function(**mapping_by_variable_name)

        output_bytestring = serializer.serialize_parameters(self.output_metadata, output_value)
        output_any = grpc_any.Any()
        output_any.value = output_bytestring
        return_value = Measurement_pb2.MeasureResponse(outputs=output_any)
        return return_value


def serve(measurement_info, configuration_parameter_list, output_parameter_list, measure_function):
    """Host the Service."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Measurement_pb2_grpc.add_MeasurementServiceServicer_to_server(
        MeasurementServiceServicer(measurement_info, configuration_parameter_list, output_parameter_list, measure_function),
        server,
    )
    port = server.add_insecure_port("[::]:0")
    server.start()
    return server, port
