"""Python Measurement Plug-In Client."""

from functools import cached_property
from pathlib import Path
from typing import List, NamedTuple

import grpc
from ni_measurement_plugin_sdk_service._internal.parameter import decoder
from ni_measurement_plugin_sdk_service._internal.parameter.metadata import ParameterMetadata
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import DoubleXYData
from _helpers import (
    _create_file_descriptor,
    _get_measure_request,
    _get_resolved_service,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient

class Output(NamedTuple):
    """Measurement result container."""

    float_out: float
    double_array_out: List[float]
    bool_out: bool
    string_out: str
    string_array_out: List[str]
    path_out: Path
    path_array_out: Path
    io_out: str
    pin_array_out: List[str]
    integer_out: int
    xy_data_out: DoubleXYData


class MeasurementPlugInClient:
    """Client for accessing the Measurement Plug-In measurement services."""
     
    def __init__(self):
        """Initialize the Measurement Plug-In client."""
        self._service_class = "ni.tests.TestMeasurement_Python"
        self._discovery_client = DiscoveryClient()
        self._metadata = self._measurement_service_stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        self._configuration_metadata = {1: ParameterMetadata(display_name='Float In', type=2, repeated=False, default_value=0.05999999865889549, annotations={}, message_type='', field_name='Float_In', enum_type=None), 2: ParameterMetadata(display_name='Double Array In', type=1, repeated=True, default_value=[0.1, 0.2, 0.3], annotations={}, message_type='', field_name='Double_Array_In', enum_type=None), 3: ParameterMetadata(display_name='Bool In', type=8, repeated=False, default_value=False, annotations={}, message_type='', field_name='Bool_In', enum_type=None), 4: ParameterMetadata(display_name='String In', type=9, repeated=False, default_value='sample string', annotations={}, message_type='', field_name='String_In', enum_type=None), 5: ParameterMetadata(display_name='String Array In', type=9, repeated=True, default_value=['String1', 'String2'], annotations={}, message_type='', field_name='String_Array_In', enum_type=None), 6: ParameterMetadata(display_name='Path In', type=9, repeated=False, default_value='path/test', annotations={'ni/type_specialization': 'path'}, message_type='', field_name='Path_In', enum_type=None), 7: ParameterMetadata(display_name='Path Array In', type=9, repeated=True, default_value=['path/test1', 'path/ntest2'], annotations={'ni/type_specialization': 'path'}, message_type='', field_name='Path_Array_In', enum_type=None), 8: ParameterMetadata(display_name='IO In', type=9, repeated=False, default_value='resource', annotations={'ni/ioresource.instrument_type': '', 'ni/type_specialization': 'ioresource'}, message_type='', field_name='IO_In', enum_type=None), 9: ParameterMetadata(display_name='Pin Array In', type=9, repeated=True, default_value=['pin1', 'pin2'], annotations={'ni/pin.instrument_type': '', 'ni/type_specialization': 'pin'}, message_type='', field_name='Pin_Array_In', enum_type=None), 10: ParameterMetadata(display_name='Integer In', type=5, repeated=False, default_value=10, annotations={}, message_type='', field_name='Integer_In', enum_type=None)}
        self._output_metadata = {1: ParameterMetadata(display_name='Float out', type=2, repeated=False, default_value=None, annotations={}, message_type='', field_name='Float_out', enum_type=None), 2: ParameterMetadata(display_name='Double Array out', type=1, repeated=True, default_value=None, annotations={}, message_type='', field_name='Double_Array_out', enum_type=None), 3: ParameterMetadata(display_name='Bool out', type=8, repeated=False, default_value=None, annotations={}, message_type='', field_name='Bool_out', enum_type=None), 4: ParameterMetadata(display_name='String out', type=9, repeated=False, default_value=None, annotations={}, message_type='', field_name='String_out', enum_type=None), 5: ParameterMetadata(display_name='String Array out', type=9, repeated=True, default_value=None, annotations={}, message_type='', field_name='String_Array_out', enum_type=None), 6: ParameterMetadata(display_name='Path Out', type=9, repeated=False, default_value=None, annotations={'ni/type_specialization': 'path'}, message_type='', field_name='Path_Out', enum_type=None), 7: ParameterMetadata(display_name='Path Array Out', type=9, repeated=True, default_value=None, annotations={'ni/type_specialization': 'path'}, message_type='', field_name='Path_Array_Out', enum_type=None), 8: ParameterMetadata(display_name='IO Out', type=9, repeated=False, default_value=None, annotations={'ni/ioresource.instrument_type': '', 'ni/type_specialization': 'ioresource'}, message_type='', field_name='IO_Out', enum_type=None), 9: ParameterMetadata(display_name='Pin Array Out', type=9, repeated=True, default_value=None, annotations={'ni/pin.instrument_type': '', 'ni/type_specialization': 'pin'}, message_type='', field_name='Pin_Array_Out', enum_type=None), 10: ParameterMetadata(display_name='Integer Out', type=5, repeated=False, default_value=None, annotations={}, message_type='', field_name='Integer_Out', enum_type=None), 11: ParameterMetadata(display_name='XY Data Out', type=11, repeated=False, default_value=None, annotations={}, message_type='ni.protobuf.types.DoubleXYData', field_name='XY_Data_Out', enum_type=None)}
        _create_file_descriptor(self._metadata, self._service_class)
        
    @cached_property
    def _measurement_service_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        resolved_service = _get_resolved_service(self._discovery_client, self._service_class)
        channel = grpc.insecure_channel(resolved_service.insecure_address)
        return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
    
    def measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = "sample string",
        string_array_in: List[str] = ['String1', 'String2'],
        path_in: Path = r"path/test",
        path_array_in: List[str] = ['path/test1', 'path/ntest2'],
        io_in: str = "resource",
        pin_array_in: List[str] = ['pin1', 'pin2'],
        integer_in: int = 10
    ) -> Output :
        """Measurement plug-in test service that performs a loopback measurement.

        Returns:
            Measurement output.
        """
        request = _get_measure_request(
            self._service_class, 
            self._configuration_metadata, 
            [float_in, double_array_in, bool_in, string_in, string_array_in, path_in, path_array_in, io_in, pin_array_in, integer_in]
        )
        result = [None] * max(self._output_metadata.keys())

        for response in self._measurement_service_stub.Measure(request):
            output_values = decoder.deserialize_parameters(
                self._output_metadata, response.outputs.value, self._service_class + ".Outputs"
            )

            for k, v in output_values.items():
                result[k - 1] = v

        return Output._make(result)
