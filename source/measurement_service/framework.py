import enum
import time
from typing import NamedTuple
import measurement_service.core.servicer as servicer
import measurement_service.core.parameter.metadata as parameter_metadata
import google.protobuf.type_pb2 as type_pb2


class MeasurementInfo(NamedTuple):
    display_name: str = None
    version: str = None
    measurement_type: str = None
    product_type: str = None
    ui_file_path: str = None
    ui_file_type: str = None


class ServiceInfo(NamedTuple):
    service_class: str
    service_id: str
    description_url: str


class DataType(enum.Enum):
    Int32 = (type_pb2.Field.TYPE_INT32, False)
    Int64 = (type_pb2.Field.TYPE_INT64, False)
    UInt32 = (type_pb2.Field.TYPE_UINT32, False)
    UInt64 = (type_pb2.Field.TYPE_UINT64, False)
    Float = (type_pb2.Field.TYPE_FLOAT, False)
    Double = (type_pb2.Field.TYPE_DOUBLE, False)
    Boolean = (type_pb2.Field.TYPE_BOOL, False)
    String = (type_pb2.Field.TYPE_STRING, False)

    Int32Array1D = (type_pb2.Field.TYPE_INT32, True)
    Int64Array1D = (type_pb2.Field.TYPE_INT64, True)
    UInt32Array1D = (type_pb2.Field.TYPE_UINT32, True)
    UInt64Array1D = (type_pb2.Field.TYPE_UINT64, True)
    FloatArray1D = (type_pb2.Field.TYPE_FLOAT, True)
    DoubleArray1D = (type_pb2.Field.TYPE_DOUBLE, True)


class Service:
    def __init__(self, measurement_info: MeasurementInfo, service_info: ServiceInfo):
        self.measurement_info: MeasurementInfo = measurement_info
        self.service_info: ServiceInfo = service_info
        self.configuration_parameter_list: list = []
        self.output_parameter_list: list = []

    def register_measurement(self, func):
        self.measure_function = func
        return func

    def configuration(self, display_name: str, type: DataType, default_value):
        grpc_field_type, repeated = type.value
        parameter = parameter_metadata.ParameterMetadata(display_name, grpc_field_type, repeated, default_value)
        self.configuration_parameter_list.append(parameter)

        def _configuration(func):
            return func

        return _configuration

    def output(self, display_name: str, type: DataType):
        grpc_field_type, repeated = type.value
        parameter = parameter_metadata.ParameterMetadata(display_name, grpc_field_type, repeated, None)
        self.output_parameter_list.append(parameter)

        def _output(func):
            return func

        return _output

    def host_as_grpc_service(self):
        if self.measure_function is None:
            raise Exception("Error, must register measurement method.")
        global server
        server, port = servicer.serve(self.measurement_info, self.configuration_parameter_list, self.output_parameter_list, self.measure_function)

        print("Hosted Service at Port:", port)

        import measurement_service.core.discoveryclient as discoveryclient
        import measurement_service.utilities.consoleexitfunctions as consoleexitfunctions

        discoveryclient.register_measurement_service(port, self.service_info, self.measurement_info.display_name)
        consoleexitfunctions.setup_unregister_on_console_close(self.close_service)

    def close_service(self):
        import measurement_service.core.discoveryclient as discoveryclient

        discoveryclient.unregister_service()
        server.stop(5)
        print("Measurement service exited.")
        time.sleep(2)
