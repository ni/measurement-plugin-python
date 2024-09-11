"""Python Measurement Plug-In Client."""

import logging
import threading
from pathlib import Path
from typing import Any, Generator, List, NamedTuple, Optional

import grpc
from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import (
    DoubleXYData,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    create_file_descriptor,
    deserialize_parameters,
    ParameterMetadata,
    serialize_parameters,
)

_logger = logging.getLogger(__name__)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


class Output(NamedTuple):
    """Measurement result container."""

    float_out: float
    double_array_out: List[float]
    bool_out: bool
    string_out: str
    string_array_out: List[str]
    path_out: Path
    path_array_out: List[Path]
    io_out: str
    io_array_out: List[str]
    integer_out: int
    xy_data_out: DoubleXYData


class NonStreamingDataMeasurementClient:
    """Client to interact with the measurement plug-in."""

    def __init__(
        self,
        *,
        discovery_client: Optional[DiscoveryClient] = None,
        grpc_channel: Optional[grpc.Channel] = None,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ):
        """Initialize the Measurement Plug-In Client.

        Args:
            discovery_client: An optional discovery client.

            grpc_channel: An optional gRPC channel targeting a measurement service.

            grpc_channel_pool: An optional gRPC channel pool.
        """
        self._initialization_lock = threading.Lock()
        self._service_class = "ni.tests.NonStreamingDataMeasurement_Python"
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._stub: Optional[v2_measurement_service_pb2_grpc.MeasurementServiceStub] = None
        self._configuration_metadata = {
            1: ParameterMetadata(
                display_name="Float In",
                type=2,
                repeated=False,
                default_value=0.05999999865889549,
                annotations={},
                message_type="",
                field_name="Float_In",
                enum_type=None,
            ),
            2: ParameterMetadata(
                display_name="Double Array In",
                type=1,
                repeated=True,
                default_value=[0.1, 0.2, 0.3],
                annotations={},
                message_type="",
                field_name="Double_Array_In",
                enum_type=None,
            ),
            3: ParameterMetadata(
                display_name="Bool In",
                type=8,
                repeated=False,
                default_value=False,
                annotations={},
                message_type="",
                field_name="Bool_In",
                enum_type=None,
            ),
            4: ParameterMetadata(
                display_name="String In",
                type=9,
                repeated=False,
                default_value='sample "string"',
                annotations={},
                message_type="",
                field_name="String_In",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="String Array In",
                type=9,
                repeated=True,
                default_value=["String1", "String2"],
                annotations={},
                message_type="",
                field_name="String_Array_In",
                enum_type=None,
            ),
            6: ParameterMetadata(
                display_name="Path In",
                type=9,
                repeated=False,
                default_value="path\test",
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_In",
                enum_type=None,
            ),
            7: ParameterMetadata(
                display_name="Path Array In",
                type=9,
                repeated=True,
                default_value=["path\test1", "path\ntest2"],
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Array_In",
                enum_type=None,
            ),
            8: ParameterMetadata(
                display_name="IO In",
                type=9,
                repeated=False,
                default_value="resource",
                annotations={
                    "ni/ioresource.instrument_type": "",
                    "ni/type_specialization": "ioresource",
                },
                message_type="",
                field_name="IO_In",
                enum_type=None,
            ),
            9: ParameterMetadata(
                display_name="IO Array In",
                type=9,
                repeated=True,
                default_value=["resource1", "resource2"],
                annotations={
                    "ni/ioresource.instrument_type": "",
                    "ni/type_specialization": "ioresource",
                },
                message_type="",
                field_name="IO_Array_In",
                enum_type=None,
            ),
            10: ParameterMetadata(
                display_name="Integer In",
                type=5,
                repeated=False,
                default_value=10,
                annotations={},
                message_type="",
                field_name="Integer_In",
                enum_type=None,
            ),
        }
        self._output_metadata = {
            1: ParameterMetadata(
                display_name="Float out",
                type=2,
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Float_out",
                enum_type=None,
            ),
            2: ParameterMetadata(
                display_name="Double Array out",
                type=1,
                repeated=True,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Double_Array_out",
                enum_type=None,
            ),
            3: ParameterMetadata(
                display_name="Bool out",
                type=8,
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Bool_out",
                enum_type=None,
            ),
            4: ParameterMetadata(
                display_name="String out",
                type=9,
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="String_out",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="String Array out",
                type=9,
                repeated=True,
                default_value=None,
                annotations={},
                message_type="",
                field_name="String_Array_out",
                enum_type=None,
            ),
            6: ParameterMetadata(
                display_name="Path Out",
                type=9,
                repeated=False,
                default_value=None,
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Out",
                enum_type=None,
            ),
            7: ParameterMetadata(
                display_name="Path Array Out",
                type=9,
                repeated=True,
                default_value=None,
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Array_Out",
                enum_type=None,
            ),
            8: ParameterMetadata(
                display_name="IO Out",
                type=9,
                repeated=False,
                default_value=None,
                annotations={
                    "ni/ioresource.instrument_type": "",
                    "ni/type_specialization": "ioresource",
                },
                message_type="",
                field_name="IO_Out",
                enum_type=None,
            ),
            9: ParameterMetadata(
                display_name="IO Array Out",
                type=9,
                repeated=True,
                default_value=None,
                annotations={
                    "ni/ioresource.instrument_type": "",
                    "ni/type_specialization": "ioresource",
                },
                message_type="",
                field_name="IO_Array_Out",
                enum_type=None,
            ),
            10: ParameterMetadata(
                display_name="Integer Out",
                type=5,
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Integer_Out",
                enum_type=None,
            ),
            11: ParameterMetadata(
                display_name="XY Data Out",
                type=11,
                repeated=False,
                default_value=None,
                annotations={},
                message_type="ni.protobuf.types.DoubleXYData",
                field_name="XY_Data_Out",
                enum_type=None,
            ),
        }
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()

    def _get_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    _logger.debug("Creating unshared GrpcChannelPool.")
                    self._grpc_channel_pool = GrpcChannelPool()
                if self._discovery_client is None:
                    _logger.debug("Creating unshared DiscoveryClient.")
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._grpc_channel_pool
                    )
                if self._stub is None:
                    service_location = self._discovery_client.resolve_service(
                        provided_interface=_V2_MEASUREMENT_SERVICE_INTERFACE,
                        service_class=self._service_class,
                    )
                    channel = self._grpc_channel_pool.get_channel(service_location.insecure_address)
                    self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        return self._stub

    def _create_file_descriptor(self) -> None:
        metadata = self._get_stub().GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
        configuration_metadata = []
        for configuration in metadata.measurement_signature.configuration_parameters:
            configuration_metadata.append(
                ParameterMetadata.initialize(
                    display_name=configuration.name,
                    type=configuration.type,
                    repeated=configuration.repeated,
                    default_value=None,
                    annotations=dict(configuration.annotations.items()),
                    message_type=configuration.message_type,
                )
            )
        output_metadata = []
        for output in metadata.measurement_signature.outputs:
            output_metadata.append(
                ParameterMetadata.initialize(
                    display_name=output.name,
                    type=output.type,
                    repeated=output.repeated,
                    default_value=None,
                    annotations=dict(output.annotations.items()),
                    message_type=output.message_type,
                )
            )
        create_file_descriptor(
            input_metadata=configuration_metadata,
            output_metadata=output_metadata,
            service_name=self._service_class,
            pool=descriptor_pool.Default(),
        )

    def _create_measure_request(
        self, parameter_values: List[Any]
    ) -> v2_measurement_service_pb2.MeasureRequest:
        serialized_configuration = any_pb2.Any(
            value=serialize_parameters(
                parameter_metadata_dict=self._configuration_metadata,
                parameter_values=parameter_values,
                service_name=f"{self._service_class}.Configurations",
            )
        )
        return v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration
        )

    def _deserialize_response(self, response: v2_measurement_service_pb2.MeasureResponse) -> Output:
        if self._output_metadata:
            result = [None] * max(self._output_metadata.keys())
        else:
            result = []
        output_values = deserialize_parameters(
            self._output_metadata, response.outputs.value, f"{self._service_class}.Outputs"
        )

        for k, v in output_values.items():
            result[k - 1] = v
        return Output._make(result)

    def _convert_paths_to_strings(self, parameter_values: List[Any]) -> List[Any]:
        result = []

        for parameter_value in parameter_values:
            # Convert each Path in the list to string and convert '\' to '\\' in strings.

            if isinstance(parameter_value, list):
                converted_list = []
                for value in parameter_value:
                    if isinstance(value, (Path, str)):
                        value = str(value).encode("unicode-escape")
                    converted_list.append(value)
                result.append(converted_list)
            elif isinstance(parameter_value, (Path, str)):
                parameter_value = str(parameter_value).encode("unicode-escape")
                result.append(parameter_value)
            else:
                result.append(parameter_value)
        return result

    def measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = 'sample "string"',
        string_array_in: List[str] = ["String1", "String2"],
        path_in: Path = "path\test",
        path_array_in: List[Path] = ["path\test1", "path\ntest2"],
        io_in: str = "resource",
        io_array_in: List[str] = ["resource1", "resource2"],
        integer_in: int = 10,
    ) -> Output:
        """Executes the Non-Streaming Data Measurement (Py).

        Returns:
            Measurement output.
        """
        parameter_values = self._convert_paths_to_strings(
            [
                float_in,
                double_array_in,
                bool_in,
                string_in,
                string_array_in,
                path_in,
                path_array_in,
                io_in,
                io_array_in,
                integer_in,
            ]
        )
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            result = self._deserialize_response(response)
        return result

    def stream_measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = 'sample "string"',
        string_array_in: List[str] = ["String1", "String2"],
        path_in: Path = "path\test",
        path_array_in: List[Path] = ["path\test1", "path\ntest2"],
        io_in: str = "resource",
        io_array_in: List[str] = ["resource1", "resource2"],
        integer_in: int = 10,
    ) -> Generator[Output, None, None]:
        """Executes the Non-Streaming Data Measurement (Py).

        Returns:
            Stream of measurement output.
        """
        parameter_values = self._convert_paths_to_strings(
            [
                float_in,
                double_array_in,
                bool_in,
                string_in,
                string_array_in,
                path_in,
                path_array_in,
                io_in,
                io_array_in,
                integer_in,
            ]
        )
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            yield self._deserialize_response(response)
