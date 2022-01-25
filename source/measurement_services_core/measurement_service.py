####################################################
# Internal Helper Measurement Services
# Not Edited by User.
####################################################

import enum
import io
import inspect
import re
import pathlib
import time
from concurrent import futures


import grpc
import google.protobuf.any_pb2 as grpc_any
import google.protobuf.wrappers_pb2 as grpc_wrappers
import google.protobuf.type_pb2 as grpc_type
import win32api
from google.protobuf.internal import encoder
from google.protobuf.internal import decoder

# By Default Import userMeasurement module as Measurement Module


import Measurement_pb2
import Measurement_pb2_grpc
import DiscoveryServices_pb2
import DiscoveryServices_pb2_grpc
import ServiceLocation_pb2


metadata = __import__("metadata")
measurement = __import__(metadata.MEASUREMENT_MODULE_NAME)


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
                DataTypeTags.double, byteIO, pos, i + 1, x.name, mapping
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


class DataTypeTags(enum.Enum):
    double = "<class 'double'>"
    bool = "<class 'bool'>"
    float = "<class 'float'>"
    integer = "<class 'int'>"
    string = "<class 'str'>"


"""
Converts Python Type literal to DataType(gRPC enum) defined in protobuf file
"""


def pyType_to_gType(typeLiteral):
    switcher = {
        DataTypeTags.bool: grpc_type.Field.Kind.TYPE_BOOL,
        DataTypeTags.float: grpc_type.Field.Kind.TYPE_FLOAT,
        DataTypeTags.integer: grpc_type.Field.Kind.TYPE_INT64,
        DataTypeTags.string: grpc_type.Field.Kind.TYPE_STRING,
    }
    return switcher.get(typeLiteral, "nothing")


"""
Serialize the value to Byte string
Returns: byteString
"""


def serialize_value(type, value):
    if type == DataTypeTags.bool:
        data = grpc_wrappers.BoolValue()
    elif type == DataTypeTags.float:
        data = grpc_wrappers.FloatValue()
    elif type == DataTypeTags.integer:
        data = grpc_wrappers.Int32Value()
    elif type == DataTypeTags.string:
        data = grpc_wrappers.StringValue()
    data.value = value
    byteString = data.SerializeToString()
    return byteString


"""
De-serialize byte string
Returns:UpdatedByteString and Value
"""


def deserialize_value(type, byteString):
    if type == DataTypeTags.bool:
        data = grpc_wrappers.BoolValue.FromString(byteString)
        removeData = grpc_wrappers.BoolValue()
    elif type == DataTypeTags.float:
        data = grpc_wrappers.FloatValue.FromString(byteString)
        removeData = grpc_wrappers.FloatValue()
    elif type == DataTypeTags.integer:
        data = grpc_wrappers.Int32Value.FromString(byteString)
        removeData = grpc_wrappers.Int32Value()
    elif type == DataTypeTags.string:
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
    if type == DataTypeTags.bool:
        coder = encoder.BoolEncoder(fieldIndex, False, False)
    elif type == DataTypeTags.float:
        coder = encoder.FloatEncoder(fieldIndex, False, False)
    elif type == DataTypeTags.integer:
        coder = encoder.Int32Encoder(fieldIndex, False, False)
    elif type == DataTypeTags.string:
        coder = encoder.StringEncoder(fieldIndex, False, False)
    coder(out_buffer.write, value)
    byteString = out_buffer.getvalue()
    return byteString


"""
De-serialize byte string based on tag. Variable Map will be updated with the Variable Value
Returns:new-position"""


def deserialize_value_with_tag(type, byteIO, pos, fieldIndex, varName, out_variableMap):
    if type == DataTypeTags.bool:
        coder = decoder.BoolDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == DataTypeTags.float:
        coder = decoder.DoubleDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif (
        type == DataTypeTags.double
    ):  # <class 'double'> is not available for python, Added as workaround for screen files.
        coder = decoder.DoubleDecoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == DataTypeTags.integer:  # Not handling Un-singed range
        coder = decoder.Int64Decoder(
            fieldIndex, False, False, varName, get_default_value
        )
    elif type == DataTypeTags.string:
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
    if type == DataTypeTags.bool:
        return False
    elif type == DataTypeTags.float:
        return 0
    elif type == DataTypeTags.integer:
        return 0
    elif type == DataTypeTags.string:
        return ""
    return None


"""
Host the Service.
"""


def serve():
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


"""
Registers the Measurement to the Discovery Service
Args:
    port: Port number of the service
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
        # Registration Request Creation
        request = DiscoveryServices_pb2.RegisterServiceRequest(
            location=service_location, service_description=service_descriptor
        )
        request.provided_services.append(metadata.PROVIDED_SERVICE)
        # Registration RPC Call
        registerRequest = stub.RegisterService(request)
        global registration_id_cache
        registration_id_cache = registerRequest.registration_id
        print("Successfully registered with DiscoveryService")
    except (grpc._channel._InactiveRpcError):
        print(
            "Unable to register with discovery service. Possible reasons : Discovery Service not Available."
        )
    return None


"""
UnRegisters the Measurement to the Discovery Service
"""


def unregister_service():
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


"""
Exit Handler to un-register measurement running in separate window exits.
"""


def on_exit(sig, func=None):
    print("Exit handler invoked")
    unregister_stop_service()


"""
Unregister Service form Discovery service and Exits the Service
"""


def unregister_stop_service():
    unregister_service()
    server.stop(2)
    print("Exiting Python Measurement Service")
    time.sleep(3)
