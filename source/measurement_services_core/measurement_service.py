"""Internal Helper Measurement Services.

Not Edited by User.
"""

import inspect
import io
import pathlib
import time
from concurrent import futures

import DiscoveryServices_pb2
import DiscoveryServices_pb2_grpc
import google.protobuf.any_pb2 as grpc_any
import google.protobuf.type_pb2 as grpc_type
import grpc
import Measurement_pb2
import Measurement_pb2_grpc
import ServiceLocation_pb2
import win32api

import parameter_serializer
from parameter_serializer import ParameterMetadata

# By Default Import userMeasurement module as Measurement Module


metadata = __import__("metadata")
measurement = __import__(metadata.MEASUREMENT_MODULE_NAME)


class MeasurementServiceImplementation(Measurement_pb2_grpc.MeasurementServiceServicer):
    """Implementation of gRPC Service - MeasurementService."""

    def __init__(self) -> None:
        super().__init__()
        self.configuration_metadata = {}
        self.output_metadata = {}

    def GetMetadata(self, request, context):  # noqa N802:inherited method names-autogen baseclass
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
            configuration_parameter.name = x.name
            # Hardcoded type to Double
            configuration_parameter.type = pythontype_to_grpctype(str(x.annotation))
            if str(x.annotation) == "<class 'list'>":
                configuration_parameter.repeated = True
            else:
                configuration_parameter.repeated = False
            measurement_parameters.configuration_parameters.append(configuration_parameter)
            parameter = ParameterMetadata(
                configuration_parameter.name,
                configuration_parameter.type,
                configuration_parameter.repeated,
            )
            self.configuration_metadata[configuration_parameter.protobuf_id] = parameter

        # Output Parameters Metadata
        # Further Scope : Update taking the data type of output
        for i, output_name in enumerate(metadata.MEASUREMENT_OUTPUTS):
            output_parameter = Measurement_pb2.Output()
            output_parameter.protobuf_id = i + 1
            output_parameter.name = output_name
            output_parameter.type = pythontype_to_grpctype(metadata.MEASUREMENT_OUTPUTS_TYPE[i])
            output_parameter.repeated = metadata.MEASUREMENT_OUTPUTS_TYPE[i] == "<class 'list'>"
            measurement_parameters.outputs.append(output_parameter)
            parameter = ParameterMetadata(
                output_parameter.name,
                output_parameter.type,
                output_parameter.repeated,
            )
            self.output_metadata[output_parameter.protobuf_id] = parameter

        # User Interface details - Framed relative to the metadata python File
        ui_details = Measurement_pb2.UserInterfaceDetails()

        metadata_base_path = str(pathlib.Path(metadata.__file__).parent.resolve())
        ui_details.configuration_ui_url = (
            metadata.SCREEN_UI_TYPE + metadata_base_path + "\\" + metadata.SCREEN_FILE_NAME
        )

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
        mapping = parameter_serializer.deserialize_parameters(
            self.configuration_metadata, byte_io.getbuffer()
        )
        # Calling the Actual Measurement here...
        output_value = measurement.measure(**mapping)

        output_bytestring = parameter_serializer.serialize_parameters(
            self.output_metadata, output_value
        )
        output_any = grpc_any.Any()
        output_any.value = output_bytestring
        return_value = Measurement_pb2.MeasureResponse(outputs=output_any)
        return return_value


def pythontype_to_grpctype(type_literal):
    """Convert Python Type literal to DataType(gRPC enum) defined in protobuf file."""
    switcher = {
        "<class 'double'>": grpc_type.Field.Kind.TYPE_DOUBLE,
        "<class 'float'>": grpc_type.Field.Kind.TYPE_DOUBLE,
        "<class 'bool'>": grpc_type.Field.Kind.TYPE_BOOL,
        "<class 'int'>": grpc_type.Field.Kind.TYPE_INT64,
        "<class 'str'>": grpc_type.Field.Kind.TYPE_STRING,
        "<class 'list'>": grpc_type.Field.Kind.TYPE_DOUBLE,
    }
    return switcher.get(type_literal, "nothing")


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
