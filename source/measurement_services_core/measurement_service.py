"""Internal Helper Measurement Services.

Not Edited by User.
"""

import enum
import inspect
import io
import pathlib
import re
import time
from concurrent import futures

import DiscoveryServices_pb2
import DiscoveryServices_pb2_grpc
import google.protobuf.any_pb2 as grpc_any
import google.protobuf.type_pb2 as grpc_type
import google.protobuf.wrappers_pb2 as grpc_wrappers
import grpc
import Measurement_pb2
import Measurement_pb2_grpc
import ServiceLocation_pb2
import win32api
from google.protobuf.internal import decoder
from google.protobuf.internal import encoder


# By Default Import userMeasurement module as Measurement Module


metadata = __import__("metadata")
measurement = __import__(metadata.MEASUREMENT_MODULE_NAME)


class MeasurementServiceImplementation(Measurement_pb2_grpc.MeasurementServiceServicer):
    """Implementation of gRPC Service - MeasurementService."""

    def GetMetadata(self, request, context):
        """RPC Method that Get the Metdata of a Measurement."""
        # Further Scope: Get Method name based on reflection
        method_name = metadata.MEASUREMENT_METHOD_NAME
        func = getattr(measurement, method_name)
        signature = inspect.signature(func)

        # measurement details
        measurement_details = Measurement_pb2.MeasurementDetails()
        measurement_details.display_name = metadata.DISPLAY_NAME
        measurement_details.version = metadata.VERSION
        measurement_details.measurement_type = metadata.MEASUREMENT_TYPE
        measurement_details.product_type = metadata.PRODUCT_TYPE

        # Measurement Parameters
        # Future Scope : Send Default Values to Clients
        measurement_parameters = Measurement_pb2.MeasurementParameters(
            configuration_parameters_messagetype="ni.measurements.v1.MeasurementConfigurations",
            outputs_message_type="ni.measurements.v1.MeasurementOutputs",
        )
        # Configurations
        for i, x in enumerate(signature.parameters.values()):
            configuration_parameter = Measurement_pb2.ConfigurationParameter()
            configuration_parameter.protobuf_id = (
                i + 1
            )  # i starts from 0 and protobuf id starts from 1
            configuration_parameter.name = snake_to_camel(x.name)
            # Hardcoded type to Double
            configuration_parameter.type = grpc_type.Field.Kind.TYPE_DOUBLE
            configuration_parameter.repeated = False
            measurement_parameters.configuration_parameters.append(configuration_parameter)

        # Output Parameters Metadata
        # Further Scope : Update taking the data type of output
        for i, output_name in enumerate(metadata.MEASUREMENT_OUTPUTS):
            output_parameter = Measurement_pb2.Output()
            output_parameter.protobuf_id = i + 1
            output_parameter.name = output_name
            output_parameter.type = grpc_type.Field.Kind.TYPE_DOUBLE
            output_parameter.repeated = False
            measurement_parameters.outputs.append(output_parameter)

        # User Interface details - Framed relative to the metadata python File
        ui_details = Measurement_pb2.UserInterfaceDetails()

        meatadata_base_path = str(pathlib.Path(metadata.__file__).parent.resolve())
        ui_details.configuration_ui_url = meatadata_base_path + "\\" + metadata.SCREEN_FILE_NAME

        # Sending back Response
        metadata_response = Measurement_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_parameters=measurement_parameters,
            user_interface_details=ui_details,
        )
        return metadata_response

    def Measure(self, request, context):
        """RPC Method that Executes the Measurement."""
        # Further Scope : Get Method name based on reflection and Store as Local Cache
        method_name = metadata.MEASUREMENT_METHOD_NAME
        func = getattr(measurement, method_name)
        signature = inspect.signature(func)
        mapping = {}
        byte_string = request.configuration_parameters.value
        byte_io = io.BytesIO()
        byte_io.write(byte_string)
        pos = 0
        for i, x in enumerate(signature.parameters.values()):
            # <class 'double'> is not available for python, Added as workaround for screen files.
            pos = deserialize_value_with_tag(
                DataTypeTags.double, byte_io, pos, i + 1, x.name, mapping
            )
        # Calling the Actual Measurement here...
        output_value = measurement.measure(**mapping)

        output_any = grpc_any.Any()
        output_byte_io = io.BytesIO()
        # Serialize the output and Sending it
        for i, output in enumerate(output_value):
            # Sending One value Implementation:
            # output_double_data = grpc_wrappers.DoubleValue()
            # output_double_data.value = output
            # output_any.value = output_any.value + output_double_data.SerializeToString()

            # Sending more than one output value:
            # output_bytestring will grow for each loop
            output_bytestring = serialize_value_with_tag(
                i + 1, DataTypeTags.double, output, output_byte_io
            )
        output_any.value = output_bytestring
        return_value = Measurement_pb2.MeasureResponse(outputs=output_any)
        return return_value


class DataTypeTags(enum.Enum):
    """Enum of datatype."""

    double = "<class 'double'>"
    bool = "<class 'bool'>"
    float = "<class 'float'>"
    integer = "<class 'int'>"
    string = "<class 'str'>"


def pythontype_to_grpctype(type_literal):
    """Convert Python Type literal to DataType(gRPC enum) defined in protobuf file."""
    switcher = {
        DataTypeTags.bool: grpc_type.Field.Kind.TYPE_BOOL,
        DataTypeTags.float: grpc_type.Field.Kind.TYPE_FLOAT,
        DataTypeTags.integer: grpc_type.Field.Kind.TYPE_INT64,
        DataTypeTags.string: grpc_type.Field.Kind.TYPE_STRING,
    }
    return switcher.get(type_literal, "nothing")


def serialize_value(type, value):
    """Serialize the value to Byte string.

    Returns: byteString
    """
    if type == DataTypeTags.bool:
        data = grpc_wrappers.BoolValue()
    elif type == DataTypeTags.float:
        data = grpc_wrappers.FloatValue()
    elif type == DataTypeTags.integer:
        data = grpc_wrappers.Int32Value()
    elif type == DataTypeTags.string:
        data = grpc_wrappers.StringValue()
    data.value = value
    byte_string = data.SerializeToString()
    return byte_string


def deserialize_value(type, byte_string):
    """De-serialize byte string.

    Returns:UpdatedByteString and Value
    """
    if type == DataTypeTags.bool:
        data = grpc_wrappers.BoolValue.FromString(byte_string)
        remove_data = grpc_wrappers.BoolValue()
    elif type == DataTypeTags.float:
        data = grpc_wrappers.FloatValue.FromString(byte_string)
        remove_data = grpc_wrappers.FloatValue()
    elif type == DataTypeTags.integer:
        data = grpc_wrappers.Int32Value.FromString(byte_string)
        remove_data = grpc_wrappers.Int32Value()
    elif type == DataTypeTags.string:
        data = grpc_wrappers.StringValue.FromString(byte_string)
        remove_data = grpc_wrappers.StringValue()
    remove_data.value = data.value
    data_string = remove_data.SerializeToString()
    updated_byte_string = byte_string.removeprefix(data_string)
    return updated_byte_string, data.value


def serialize_value_with_tag(field_index, type, value, out_buffer):
    """Serialize the value to Byte string based on tag.

    Returns: byteString
    """
    if type == DataTypeTags.bool:
        coder = encoder.BoolEncoder(field_index, False, False)
    elif type == DataTypeTags.float:
        coder = encoder.FloatEncoder(field_index, False, False)
    elif type == DataTypeTags.double:
        coder = encoder.DoubleEncoder(field_index, False, False)
    elif type == DataTypeTags.integer:
        coder = encoder.Int32Encoder(field_index, False, False)
    elif type == DataTypeTags.string:
        coder = encoder.StringEncoder(field_index, False, False)
    coder(out_buffer.write, value)
    byte_string = out_buffer.getvalue()
    return byte_string


def deserialize_value_with_tag(type, byte_io, pos, field_index, variable_name, out_variable_map):
    """De-serialize byte string based on tag. Variable Map will be updated with the Variable Value.

    Returns:new-position
    """
    if type == DataTypeTags.bool:
        coder = decoder.BoolDecoder(field_index, False, False, variable_name, get_default_value)
    elif type == DataTypeTags.float:
        coder = decoder.DoubleDecoder(field_index, False, False, variable_name, get_default_value)
    elif (
        type == DataTypeTags.double
    ):  # <class 'double'> is not available for python, Added as workaround for screen files.
        coder = decoder.DoubleDecoder(field_index, False, False, variable_name, get_default_value)
    elif type == DataTypeTags.integer:  # Not handling Un-singed range
        coder = decoder.Int64Decoder(field_index, False, False, variable_name, get_default_value)
    elif type == DataTypeTags.string:
        coder = decoder.StringDecoder(field_index, False, False, variable_name, get_default_value)
    new_pos = coder(
        byte_io.getbuffer(),
        pos + encoder._TagSize(field_index),
        byte_io.__sizeof__(),
        type,
        out_variable_map,
    )
    return new_pos


def camel_to_snake(string_value):
    """Convert a string from camel case to snake case."""
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", string_value).lower()


def snake_to_camel(string_value):
    """Convert a string from snake case to camel case."""
    return_value = "".join(word.title() for word in string_value.split("_"))
    return return_value


def get_default_value(type):
    """Get the default value of data type."""
    if type == DataTypeTags.bool:
        return False
    elif type == DataTypeTags.float:
        return 0
    elif type == DataTypeTags.integer:
        return 0
    elif type == DataTypeTags.string:
        return ""
    return None


def serve():
    """Host the Service."""
    global server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Measurement_pb2_grpc.add_MeasurementServiceServicer_to_server(
        MeasurementServiceImplementation(), server
    )
    port = server.add_insecure_port("[::]:0")
    server.start()
    win32api.SetConsoleCtrlHandler(on_exit, True)
    print("Hosted Python Measurement as Service at Port:", port)
    register_service(port)
    return None


def register_service(port):
    """Register the Measurement to the Discovery Service.

    Args:
    ----
        port: Port number of the service


    """
    try:
        channel = grpc.insecure_channel("localhost:42000")
        stub = DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)
        # Service Location
        service_location = ServiceLocation_pb2.ServiceLocation()
        service_location.location = "localhost"
        service_location.insecure_port = str(port)
        # Service Descriptor
        service_descriptor = DiscoveryServices_pb2.ServiceDescriptor()
        service_descriptor.service_id = metadata.SERVICE_ID
        service_descriptor.name = metadata.DISPLAY_NAME
        service_descriptor.service_class = metadata.SERVICE_CLASS
        service_descriptor.description_url = metadata.DESCRIPTION_URL
        # Registration Request Creation
        request = DiscoveryServices_pb2.RegisterServiceRequest(
            location=service_location, service_description=service_descriptor
        )
        request.provided_services.append(metadata.PROVIDED_SERVICE)
        # Registration RPC Call
        register_request = stub.RegisterService(request)
        global registration_id_cache
        registration_id_cache = register_request.registration_id
        print("Successfully registered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to register with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None


def unregister_service():
    """Un-Register the Measurement to the Discovery Service."""
    try:
        channel = grpc.insecure_channel("localhost:42000")
        stub = DiscoveryServices_pb2_grpc.RegistryServiceStub(channel)

        # Un-registration Request Creation
        request = DiscoveryServices_pb2.UnregisterServiceRequest(
            registration_id=registration_id_cache
        )
        # Un-registration RPC Call
        stub.UnregisterService(request)
        print("Successfully unregistered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to unregister with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None


def on_exit(sig, func=None):
    """Exit Handler to un-register measurement running in separate window exits."""
    print("Exit handler invoked")
    unregister_stop_service()


def unregister_stop_service():
    """Unregister Service form Discovery service and Exits the Service."""
    unregister_service()
    server.stop(2)
    print("Exiting Python Measurement Service")
    time.sleep(3)
