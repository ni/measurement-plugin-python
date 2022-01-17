####################################################
# Internal Helper Measurement Services
# Not Edited by User.
####################################################

import io
import inspect
import re
import pathlib
from concurrent import futures


import grpc
import google.protobuf.any_pb2 as grpc_any
import google.protobuf.wrappers_pb2 as grpc_wrappers
import google.protobuf.type_pb2 as grpc_type
from google.protobuf.internal import encoder
from google.protobuf.internal import decoder

# By Default Import userMeasurement module as Measurement Module
import measurement
import metadata
import Measurement_pb2
import Measurement_pb2_grpc
import DiscoveryServices_pb2
import DiscoveryServices_pb2_grpc
import ServiceLocation_pb2


class MeasurementServiceImplementation(Measurement_pb2_grpc.MeasurementServiceServicer):
    def GetMetadata(self, request, context):
        # Further Scope: Get Method name based on reflection
        methodName = metadata.MEASUREMENT_METHOD_NAME
        func = getattr(measurement, methodName)
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
            configuration_parameter.protobuf_id = i + 1
            configuration_parameter.name = snake_to_camel(x.name)
            # Hardcoded type to Double
            configuration_parameter.type = grpc_type.Field.Kind.TYPE_DOUBLE
            configuration_parameter.repeated = False
            measurement_parameters.configuration_parameters.append(
                configuration_parameter
            )

        # Output Parameters Metadata - Hardcoded - Further Scope - get this info from the User(May be via a config file)
        output_parameter1 = Measurement_pb2.Output()
        output_parameter1.protobuf_id = 1
        output_parameter1.name = "VoltageMeasurement"
        output_parameter1.type = grpc_type.Field.Kind.TYPE_DOUBLE
        output_parameter1.repeated = False

        measurement_parameters.outputs.append(output_parameter1)

        # User Interface details - Framed relative to the metadata python File
        ui_details = Measurement_pb2.UserInterfaceDetails()

        meatadata_base_path = str(pathlib.Path(metadata.__file__).parent.resolve())
        ui_details.configuration_ui_url = (
            meatadata_base_path + "\\" + metadata.SCREEN_FILE_NAME
        )

        # Sending back Response
        metadata_response = Measurement_pb2.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_parameters=measurement_parameters,
            user_interface_details=ui_details,
        )
        return metadata_response

    def Measure(self, request, context):
        # Further Scope : Get Method name based on reflection and Store as Local Cache
        methodName = metadata.MEASUREMENT_METHOD_NAME
        func = getattr(measurement, methodName)
        signature = inspect.signature(func)
        mapping = {}
        byteString = request.configuration_parameters.value
        byteIO = io.BytesIO()
        byteIO.write(byteString)
        pos = 0
        for i, x in enumerate(signature.parameters.values()):
            # <class 'double'> is not available for python, Added as workaround for screen files.
            pos = deserialize_value_with_tag(
                "<class 'double'>", byteIO, pos, i + 1, x.name, mapping
            )
        # Calling the Actual Measurement here...
        outputValue = measurement.measure(**mapping)

        # Serialize the output and Sending it
        output_any = grpc_any.Any()
        outputDoubleData = grpc_wrappers.DoubleValue()
        outputDoubleData.value = outputValue
        output_any.value = outputDoubleData.SerializeToString()
        returnValue = Measurement_pb2.MeasureResponse(outputs=output_any)
        return returnValue


"""
Converts Python Type literal to DataType(gRPC enum) defined in protobuf file
"""


def pyType_to_gType(typeLiteral):
    switcher = {
        "<class 'bool'>": grpc_type.Field.Kind.TYPE_BOOL,
        "<class 'float'>": grpc_type.Field.Kind.TYPE_FLOAT,
        "<class 'int'>": grpc_type.Field.Kind.TYPE_INT32,
        "<class 'str'>": grpc_type.Field.Kind.TYPE_STRING,
    }
    return switcher.get(typeLiteral, "nothing")


"""
Serialize the value to Byte string
Returns: byteString
"""


def serialize_value(type, value):
    if type == "<class 'bool'>":
        data = grpc_wrappers.BoolValue()
    elif type == "<class 'float'>":
        data = grpc_wrappers.FloatValue()
    elif type == "<class 'int'>":
        data = grpc_wrappers.Int32Value()
    elif type == "<class 'str'>":
        data = grpc_wrappers.StringValue()
    data.value = value
    byteString = data.SerializeToString()
    return byteString


"""
De-serialize byte string
Returns:UpdatedByteString and Value
"""


def deserialize_value(type, byteString):
    if type == "<class 'bool'>":
        data = grpc_wrappers.BoolValue.FromString(byteString)
        removeData = grpc_wrappers.BoolValue()
    elif type == "<class 'float'>":
        data = grpc_wrappers.FloatValue.FromString(byteString)
        removeData = grpc_wrappers.FloatValue()
    elif type == "<class 'int'>":
        data = grpc_wrappers.Int32Value.FromString(byteString)
        removeData = grpc_wrappers.Int32Value()
    elif type == "<class 'str'>":
        data = grpc_wrappers.StringValue.FromString(byteString)
        removeData = grpc_wrappers.StringValue()
    removeData.value = data.value
    dataString = removeData.SerializeToString()
    updatedByteString = byteString.removeprefix(dataString)
    return updatedByteString, data.value


"""
Serialize the value to Byte string based on tag
Returns: byteString
"""


def serialize_value_with_tag(fieldIndex, type, value, out_buffer):
    if type == "<class 'bool'>":
        coder = encoder.BoolEncoder(fieldIndex, False, False)
    elif type == "<class 'float'>":
        coder = encoder.FloatEncoder(fieldIndex, False, False)
    elif type == "<class 'int'>":
        coder = encoder.Int32Encoder(fieldIndex, False, False)
    elif type == "<class 'str'>":
        coder = encoder.StringEncoder(fieldIndex, False, False)
    coder(out_buffer.write, value)
    byteString = out_buffer.getvalue()
    return byteString


"""
De-serialize byte string based on tag. Variable Map will be updated with the Variable Value
Returns:new-position"""


def deserialize_value_with_tag(type, byteIO, pos, fieldIndex, varName, out_variableMap):
    if type == "<class 'bool'>":
        coder = decoder.BoolDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == "<class 'float'>":
        coder = decoder.DoubleDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif (
        type == "<class 'double'>"
    ):  # <class 'double'> is not available for python, Added as workaround for screen files.
        coder = decoder.DoubleDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == "<class 'int'>":  # Not handling Un-singed range
        coder = decoder.Int64Decoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == "<class 'str'>":
        coder = decoder.StringDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    new_pos = coder(
        byteIO.getbuffer(),
        pos + encoder._TagSize(fieldIndex),
        byteIO.__sizeof__(),
        type,
        out_variableMap,
    )
    return new_pos


def camel_to_snake(stringValue):
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", stringValue).lower()


def snake_to_camel(stringValue):
    returnValue = "".join(word.title() for word in stringValue.split("_"))
    return returnValue


def get_default_value(type):
    if type == "<class 'bool'>":
        return False
    elif type == "<class 'float'>":
        return 0
    elif type == "<class 'int'>":
        return 0
    elif type == "<class 'str'>":
        return ""
    return None


"""
Host the Service.
"""


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Measurement_pb2_grpc.add_MeasurementServiceServicer_to_server(
        MeasurementServiceImplementation(), server
    )
    port = server.add_insecure_port("[::]:0")
    server.start()
    print("Hosted Python Measurement as Service at Port:", port)
    register_service(port)
    server.wait_for_termination()
    return None


"""
Registers the Measurement to the Discovery Service
"""


def register_service(port):
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
        # Request Creation
        request = DiscoveryServices_pb2.RegisterServiceRequest(
            location=service_location, service_description=service_descriptor
        )
        request.provided_services.append(metadata.PROVIDED_SERVICE)
        # Register RPC Call
        stub.RegisterService(request)
        print("Successfully registered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to register with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None
