"""Generated client API for the 'Non-Streaming Data Measurement (Py)' measurement plug-in."""

import logging
import pathlib
import threading
from enum import Enum
from pathlib import Path
from typing import Any, Generator, Iterable, List, NamedTuple, Optional

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
from ni_measurement_plugin_sdk_service.pin_map import PinMapClient
from ni_measurement_plugin_sdk_service.session_management import PinMapContext

_logger = logging.getLogger(__name__)

_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


class EnumInEnum(Enum):
    """EnumInEnum used for enum-typed measurement configs and outputs."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class ProtobufEnumInEnum(Enum):
    """ProtobufEnumInEnum used for enum-typed measurement configs and outputs."""

    NONE = 0
    PINK = 1
    WHITE = 2
    BLACK = 3


class Outputs(NamedTuple):
    """Outputs for the 'Non-Streaming Data Measurement (Py)' measurement plug-in."""

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
    enum_out: EnumInEnum
    enum_array_out: List[EnumInEnum]
    protobuf_enum_out: ProtobufEnumInEnum


class NonStreamingDataMeasurementClient:
    """Client for the 'Non-Streaming Data Measurement (Py)' measurement plug-in."""

    def __init__(
        self,
        *,
        discovery_client: Optional[DiscoveryClient] = None,
        pin_map_client: Optional[PinMapClient] = None,
        grpc_channel: Optional[grpc.Channel] = None,
        grpc_channel_pool: Optional[GrpcChannelPool] = None,
    ):
        """Initialize the Measurement Plug-In Client.

        Args:
            discovery_client: An optional discovery client.

            pin_map_client: An optional pin map client.

            grpc_channel: An optional gRPC channel targeting a measurement service.

            grpc_channel_pool: An optional gRPC channel pool.
        """
        self._initialization_lock = threading.RLock()
        self._service_class = "ni.tests.NonStreamingDataMeasurement_Python"
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._pin_map_client = pin_map_client
        self._stub: Optional[v2_measurement_service_pb2_grpc.MeasurementServiceStub] = None
        self._measure_response: Optional[
            Generator[v2_measurement_service_pb2.MeasureResponse, None, None]
        ] = None
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
                default_value="sample string",
                annotations={},
                message_type="",
                field_name="String_In",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="String Array In",
                type=9,
                repeated=True,
                default_value=[
                    "string with /forwardslash",
                    "string with \\backslash",
                    "string with 'single quotes'",
                    'string with "double quotes"',
                    "string with \ttabspace",
                    "string with \nnewline",
                ],
                annotations={},
                message_type="",
                field_name="String_Array_In",
                enum_type=None,
            ),
            6: ParameterMetadata(
                display_name="Path In",
                type=9,
                repeated=False,
                default_value="sample\\path\\for\\test",
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_In",
                enum_type=None,
            ),
            7: ParameterMetadata(
                display_name="Path Array In",
                type=9,
                repeated=True,
                default_value=[
                    "path/with/forward/slash",
                    "path\\with\\backslash",
                    "path with 'single quotes'",
                    'path with "double quotes"',
                    "path\twith\ttabs",
                    "path\nwith\nnewlines",
                ],
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
            11: ParameterMetadata(
                display_name="Enum In",
                type=14,
                repeated=False,
                default_value=3,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_In",
                enum_type=EnumInEnum,
            ),
            12: ParameterMetadata(
                display_name="Enum Array In",
                type=14,
                repeated=True,
                default_value=[1, 2],
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_Array_In",
                enum_type=EnumInEnum,
            ),
            13: ParameterMetadata(
                display_name="Protobuf Enum In",
                type=14,
                repeated=False,
                default_value=3,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "PINK": 1, "WHITE": 2, "BLACK": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Protobuf_Enum_In",
                enum_type=ProtobufEnumInEnum,
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
            12: ParameterMetadata(
                display_name="Enum Out",
                type=14,
                repeated=False,
                default_value=None,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_Out",
                enum_type=EnumInEnum,
            ),
            13: ParameterMetadata(
                display_name="Enum Array Out",
                type=14,
                repeated=True,
                default_value=None,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_Array_Out",
                enum_type=EnumInEnum,
            ),
            14: ParameterMetadata(
                display_name="Protobuf Enum out",
                type=14,
                repeated=False,
                default_value=None,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "PINK": 1, "WHITE": 2, "BLACK": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Protobuf_Enum_out",
                enum_type=ProtobufEnumInEnum,
            ),
        }
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()
        self._pin_map_context: Optional[PinMapContext] = None

    @property
    def pin_map_context(self) -> PinMapContext:
        """The pin map context for the measurement."""
        return self._pin_map_context

    @pin_map_context.setter
    def pin_map_context(self, val: PinMapContext) -> None:
        if not isinstance(val, PinMapContext):
            raise TypeError(
                f"Invalid type {type(val)}: The given value must be an instance of PinMapContext."
            )
        self._pin_map_context = val

    @property
    def sites(self) -> List[int]:
        """The sites where the measurement must be executed."""
        if self._pin_map_context is not None:
            return self._pin_map_context.sites

    @sites.setter
    def sites(self, val: List[int]) -> None:
        if self._pin_map_context is None:
            raise AttributeError(
                "Cannot set sites because the pin map context is None. Please provide a pin map context or register a pin map before setting sites."
            )
        self._pin_map_context = self._pin_map_context._replace(sites=val)

    def _get_stub(self) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
        if self._stub is None:
            with self._initialization_lock:
                if self._stub is None:
                    service_location = self._get_discovery_client().resolve_service(
                        provided_interface=_V2_MEASUREMENT_SERVICE_INTERFACE,
                        service_class=self._service_class,
                    )
                    channel = self._get_grpc_channel_pool().get_channel(
                        service_location.insecure_address
                    )
                    self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)
        return self._stub

    def _get_discovery_client(self) -> DiscoveryClient:
        if self._discovery_client is None:
            with self._initialization_lock:
                if self._discovery_client is None:
                    self._discovery_client = DiscoveryClient(
                        grpc_channel_pool=self._get_grpc_channel_pool(),
                    )
        return self._discovery_client

    def _get_grpc_channel_pool(self) -> GrpcChannelPool:
        if self._grpc_channel_pool is None:
            with self._initialization_lock:
                if self._grpc_channel_pool is None:
                    self._grpc_channel_pool = GrpcChannelPool()
        return self._grpc_channel_pool

    def _get_pin_map_client(self) -> PinMapClient:
        if self._pin_map_client is None:
            with self._initialization_lock:
                if self._pin_map_client is None:
                    self._pin_map_client = PinMapClient(
                        discovery_client=self._get_discovery_client(),
                        grpc_channel_pool=self._get_grpc_channel_pool(),
                    )
        return self._pin_map_client

    def _create_file_descriptor(self) -> None:
        create_file_descriptor(
            input_metadata=list(self._configuration_metadata.values()),
            output_metadata=list(self._output_metadata.values()),
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
            configuration_parameters=serialized_configuration,
            pin_map_context=self._pin_map_context._to_grpc() if self._pin_map_context else None,
        )

    def _deserialize_response(
        self, response: v2_measurement_service_pb2.MeasureResponse
    ) -> Outputs:
        if self._output_metadata:
            result = [None] * max(self._output_metadata.keys())
        else:
            result = []
        output_values = deserialize_parameters(
            self._output_metadata, response.outputs.value, f"{self._service_class}.Outputs"
        )

        for k, v in output_values.items():
            result[k - 1] = v
        return Outputs._make(result)

    def measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = "sample string",
        string_array_in: List[str] = [
            "string with /forwardslash",
            "string with \\backslash",
            "string with 'single quotes'",
            'string with "double quotes"',
            "string with \ttabspace",
            "string with \nnewline",
        ],
        path_in: Path = Path("sample\\path\\for\\test"),
        path_array_in: List[Path] = [
            Path("path/with/forward/slash"),
            Path("path\\with\\backslash"),
            Path("path with 'single quotes'"),
            Path('path with "double quotes"'),
            Path("path\twith\ttabs"),
            Path("path\nwith\nnewlines"),
        ],
        io_in: str = "resource",
        io_array_in: List[str] = ["resource1", "resource2"],
        integer_in: int = 10,
        enum_in: EnumInEnum = EnumInEnum.BLUE,
        enum_array_in: List[EnumInEnum] = [EnumInEnum.RED, EnumInEnum.GREEN],
        protobuf_enum_in: ProtobufEnumInEnum = ProtobufEnumInEnum.BLACK,
    ) -> Outputs:
        """Perform a single measurement.

        Returns:
            Measurement outputs.
        """
        stream_measure_response = self.stream_measure(
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
            enum_in,
            enum_array_in,
            protobuf_enum_in,
        )
        for response in stream_measure_response:
            result = response
        return result

    def stream_measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = "sample string",
        string_array_in: List[str] = [
            "string with /forwardslash",
            "string with \\backslash",
            "string with 'single quotes'",
            'string with "double quotes"',
            "string with \ttabspace",
            "string with \nnewline",
        ],
        path_in: Path = Path("sample\\path\\for\\test"),
        path_array_in: List[Path] = [
            Path("path/with/forward/slash"),
            Path("path\\with\\backslash"),
            Path("path with 'single quotes'"),
            Path('path with "double quotes"'),
            Path("path\twith\ttabs"),
            Path("path\nwith\nnewlines"),
        ],
        io_in: str = "resource",
        io_array_in: List[str] = ["resource1", "resource2"],
        integer_in: int = 10,
        enum_in: EnumInEnum = EnumInEnum.BLUE,
        enum_array_in: List[EnumInEnum] = [EnumInEnum.RED, EnumInEnum.GREEN],
        protobuf_enum_in: ProtobufEnumInEnum = ProtobufEnumInEnum.BLACK,
    ) -> Generator[Outputs, None, None]:
        """Perform a streaming measurement.

        Returns:
            Stream of measurement outputs.
        """
        parameter_values = _convert_paths_to_strings(
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
                enum_in,
                enum_array_in,
                protobuf_enum_in,
            ]
        )
        with self._initialization_lock:
            if self._measure_response is not None:
                raise RuntimeError(
                    "A measurement is currently in progress. To make concurrent measurement requests, please create a new client instance."
                )
            request = self._create_measure_request(parameter_values)
            self._measure_response = self._get_stub().Measure(request)
        try:
            for response in self._measure_response:
                yield self._deserialize_response(response)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                _logger.debug("The measurement is canceled.")
            raise
        finally:
            with self._initialization_lock:
                self._measure_response = None

    def cancel(self) -> bool:
        """Cancels the active measurement call."""
        with self._initialization_lock:
            if self._measure_response:
                return self._measure_response.cancel()
            else:
                return False

    def register_pin_map(self, pin_map_path: pathlib.Path) -> None:
        """Registers the pin map with the pin map service.

        Args:
            pin_map_path: Absolute path of the pin map file.
        """
        pin_map_id = self._get_pin_map_client().update_pin_map(pin_map_path)
        if self._pin_map_context is None:
            self._pin_map_context = PinMapContext(pin_map_id=pin_map_id, sites=[0])
        else:
            self._pin_map_context = self._pin_map_context._replace(pin_map_id=pin_map_id)


def _convert_paths_to_strings(parameter_values: Iterable[Any]) -> List[Any]:
    result: List[Any] = []

    for parameter_value in parameter_values:
        if isinstance(parameter_value, list):
            converted_list = []
            for value in parameter_value:
                if isinstance(value, Path):
                    converted_list.append(str(value))
                else:
                    converted_list.append(value)
            result.append(converted_list)
        elif isinstance(parameter_value, Path):
            result.append(str(parameter_value))
        else:
            result.append(parameter_value)
    return result
