####################################################
# Internal Helper Measurement Services
# Not Edited by User.
####################################################
import io
import inspect
import re
from concurrent import futures

import grpc
import google.protobuf.any_pb2 as grpc_any
import google.protobuf.wrappers_pb2 as grpc_wrapper
from google.protobuf.internal import encoder
from google.protobuf.internal import decoder

# By Default Import userMeasurement module as Measurement Module
import measurement
from core import DiscoveryServices_pb2_grpc as ds_stub
from core import DiscoveryServices_pb2 as ds_message
from core import ServiceLocation_pb2 as sl_message
from core import Measurement_pb2_grpc as ms_stub
from core import Measurement_pb2 as ms_message


class MeasurementServiceImplementation(ms_stub.MeasurementServiceServicer):
    def GetMetadata(self, request, context):
        methodName = "measure"  # Further Scope: Get Method name based on reflection
        func = getattr(measurement, methodName)
        signature = inspect.signature(func)

        # measurement details
        measurement_details = ms_message.MeasurementDetails()
        measurement_details.display_name = "DCMeasurement"
        measurement_details.version = "0.0.0.1"
        measurement_details.measurement_type = "DC"
        measurement_details.product_type = "ADC"

        # Measurement Parameters
        measurement_parameters = ms_message.MeasurementParameters(
            configuration_parameters_messagetype="Measurement_v1.MeasurementConfigurations",
            outputs_messagetype="Measurement_v1.MeasurementOutputs",
        )
        # Configurations
        for i, x in enumerate(signature.parameters.values()):
            configuration_parameter = ms_message.ConfigurationParameter()
            configuration_parameter.protobuf_id = i + 1
            configuration_parameter.name = snake_to_camel(x.name)
            # Hardcoded type to Double
            configuration_parameter.type = ms_message.Type.TYPE_DOUBLE
            configuration_parameter.repeated = False
            measurement_parameters.configuration_parameters.append(
                configuration_parameter
            )

        # Output Parameters Metadata - Hardcoded - Further Scope - get this info from the User(May be via a config file)
        output_parameter1 = ms_message.Output()
        output_parameter1.protobuf_id = 1
        output_parameter1.name = "VoltageMeasurement"
        output_parameter1.type = ms_message.Type.TYPE_DOUBLE
        output_parameter1.repeated = False

        measurement_parameters.outputs.append(output_parameter1)

        # User Interface details
        ui_details = ms_message.UserInterfaceDetails()
        ui_details.configuration_ui_url = "C:\\Users\\vasanthakumar\\Desktop\\DCMeasurementScreen.isscr"  # Change to relative path

        # Sending back Response
        metadata_response = ms_message.GetMetadataResponse(
            measurement_details=measurement_details,
            measurement_parameters=measurement_parameters,
            user_interface_details=ui_details,
        )
        return metadata_response

    def Measure(self, request, context):
        methodName = "measure"  # Further Scope : Get Method name based on reflection and Store as Local Cache
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
        output = grpc_any.Any()
        outputDoubleData = grpc_wrapper.DoubleValue()
        outputDoubleData.value = outputValue
        output.value = outputDoubleData.SerializeToString()
        measurement_value = ms_message.MeasurementValue(any=output)
        error_value = ms_message.ErrorInformation(is_error=False)
        returnValue = ms_message.MeasureResponse(
            outputs=[measurement_value], error=error_value
        )
        return returnValue


"""
Converts Python Type literal to DataType(gRPC enum) defined in protobuf file
"""


def pyType_to_gType(typeLiteral):
    switcher = {
        "<class 'bool'>": ms_message.Type.TYPE_BOOL,
        "<class 'float'>": ms_message.Type.TYPE_FLOAT,
        "<class 'int'>": ms_message.Type.TYPE_INT32,
        "<class 'str'>": ms_message.Type.TYPE_STRING,
    }
    return switcher.get(typeLiteral, "nothing")


"""
Serialize the value to Byte string
Returns: byteString
"""


def serialize_value(type, value):
    if type == "<class 'bool'>":
        data = grpc_wrapper.BoolValue()
    elif type == "<class 'float'>":
        data = grpc_wrapper.FloatValue()
    elif type == "<class 'int'>":
        data = grpc_wrapper.Int32Value()
    elif type == "<class 'str'>":
        data = grpc_wrapper.StringValue()
    data.value = value
    byteString = data.SerializeToString()
    return byteString


"""
De-serialize byte string
Returns:UpdatedByteString and Value
"""


def deserialize_value(type, byteString):
    if type == "<class 'bool'>":
        data = grpc_wrapper.BoolValue.FromString(byteString)
        removeData = grpc_wrapper.BoolValue()
    elif type == "<class 'float'>":
        data = grpc_wrapper.FloatValue.FromString(byteString)
        removeData = grpc_wrapper.FloatValue()
    elif type == "<class 'int'>":
        data = grpc_wrapper.Int32Value.FromString(byteString)
        removeData = grpc_wrapper.Int32Value()
    elif type == "<class 'str'>":
        data = grpc_wrapper.StringValue.FromString(byteString)
        removeData = grpc_wrapper.StringValue()
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
Returns:new-position 
"""


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
    ms_stub.add_MeasurementServiceServicer_to_server(
        MeasurementServiceImplementation(), server
    )
    port = server.add_insecure_port("[::]:0")
    server.start()
    register_service(port)
    print("Hosting Python Measurement as Service at", port)
    server.wait_for_termination()
    return None


"""
Registers the Measurement to the Discovery Service
"""


def register_service(port):
    channel = grpc.insecure_channel("localhost:42000")
    stub = ds_stub.RegistryServiceStub(channel)
    # Service Location
    service_location = sl_message.ServiceLocation()
    service_location.location = "localhost"
    service_location.insecure_port = str(port)
    # Service Descriptor
    service_descriptor = ds_message.ServiceDescriptor()
    service_descriptor.service_id = "{B290B571-CB76-426F-9ACC-5168DC1B027C}"
    service_descriptor.name = "DCMeasurement(Python)"
    service_descriptor.service_class = "DCMeasurementPython"
    service_descriptor.description_url = (
        "https://www.ni.com/measurementservices/dcmeasurement.html"
    )
    # Request Creation
    request = ds_message.RegisterServiceRequest(
        location=service_location, service_description=service_descriptor
    )
    request.provided_services.append("MeasurementService")
    # Register RPC Call
    stub.RegisterService(request)
    print("Successfully registered with DiscoveryService")
