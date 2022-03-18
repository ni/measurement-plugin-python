import time
import nimf.internal.servicer as servicer
import nimf.internal.parameter.metadata as parameter_metadata

import nimf.internal.utilities.consoleexitfunctions as consoleexitfunctions
from nimf.measurement.info import MeasurementInfo, ServiceInfo, DataType
import nimf.internal.discoveryclient as discoveryclient


class MeasurementService:
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

        discoveryclient.register_measurement_service(port, self.service_info, self.measurement_info.display_name)
        consoleexitfunctions.setup_unregister_on_console_close(self.close_service)

    def close_service(self):

        discoveryclient.unregister_service()
        server.stop(5)
        print("Measurement service exited.")
        time.sleep(2)
