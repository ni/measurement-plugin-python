"""Generated client API for the '本地化测量（Py）' measurement plug-in."""

from __future__ import annotations

import logging
import pathlib
import threading
import typing
import warnings
from enum import Enum

import grpc
from google.protobuf import any_pb2, descriptor_pool
from google.protobuf.type_pb2 import Field
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.array_pb2 import (
    Double2DArray,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.array_pb2 import (
    String2DArray,
)
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types.xydata_pb2 import (
    DoubleXYData,
)
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool
from ni_measurement_plugin_sdk_service.measurement import WrongMessageTypeWarning
from ni_measurement_plugin_sdk_service.measurement.client_support import (
    ParameterMetadata,
    create_file_descriptor,
    deserialize_parameters,
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


class Outputs(typing.NamedTuple):
    """Outputs for the '本地化测量（Py）' measurement plug-in."""

    float_out: float
    double_array_out: typing.Sequence[float]
    bool_out: bool
    string_out: str
    string_array_out: typing.Sequence[str]
    path_out: pathlib.Path
    path_array_out: typing.Sequence[pathlib.Path]
    io_out: str
    io_array_out: typing.Sequence[str]
    integer_out: int
    xy_data_out: DoubleXYData
    enum_out: EnumInEnum
    enum_array_out: typing.Sequence[EnumInEnum]
    double_2d_array_out: Double2DArray
    string_2d_array_out: String2DArray


class LocalizedMeasurementClient:
    """Client for the '本地化测量（Py）' measurement plug-in."""

    def __init__(
        self,
        *,
        discovery_client: DiscoveryClient | None = None,
        pin_map_client: PinMapClient | None = None,
        grpc_channel: grpc.Channel | None = None,
        grpc_channel_pool: GrpcChannelPool | None = None,
    ):
        """Initialize the Measurement Plug-In Client.

        Args:
            discovery_client: An optional discovery client.

            pin_map_client: An optional pin map client.

            grpc_channel: An optional gRPC channel targeting a measurement service.

            grpc_channel_pool: An optional gRPC channel pool.
        """
        self._initialization_lock = threading.RLock()
        self._service_class = "ni.tests.LocalizedMeasurement_Python"
        self._version = "0.1.0.0"
        self._grpc_channel_pool = grpc_channel_pool
        self._discovery_client = discovery_client
        self._pin_map_client = pin_map_client
        self._stub: v2_measurement_service_pb2_grpc.MeasurementServiceStub | None = None
        self._measure_response: None | (
            grpc.CallIterator[v2_measurement_service_pb2.MeasureResponse]
        ) = None
        self._configuration_metadata = {
            1: ParameterMetadata(
                display_name="Float In",
                type=Field.Kind.ValueType(2),
                repeated=False,
                default_value=0.05999999865889549,
                annotations={},
                message_type="",
                field_name="Float_In",
                enum_type=None,
            ),
            2: ParameterMetadata(
                display_name="Double Array In",
                type=Field.Kind.ValueType(1),
                repeated=True,
                default_value=[0.1, 0.2, 0.3],
                annotations={},
                message_type="",
                field_name="Double_Array_In",
                enum_type=None,
            ),
            3: ParameterMetadata(
                display_name="Bool In",
                type=Field.Kind.ValueType(8),
                repeated=False,
                default_value=False,
                annotations={},
                message_type="",
                field_name="Bool_In",
                enum_type=None,
            ),
            4: ParameterMetadata(
                display_name="String In",
                type=Field.Kind.ValueType(9),
                repeated=False,
                default_value="示例字符串",
                annotations={},
                message_type="",
                field_name="String_In",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="String Array In",
                type=Field.Kind.ValueType(9),
                repeated=True,
                default_value=[
                    "带有/正斜杠的字符串",
                    "带有\\反斜杠的字符串",
                    "带有'单引号'的字符串",
                    '带有"双引号"的字符串',
                    "带有\t制表符的字符串",
                    "带有\n换行符的字符串",
                ],
                annotations={},
                message_type="",
                field_name="String_Array_In",
                enum_type=None,
            ),
            6: ParameterMetadata(
                display_name="Path In",
                type=Field.Kind.ValueType(9),
                repeated=False,
                default_value="示例\\路径\\用于\\测试",
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_In",
                enum_type=None,
            ),
            7: ParameterMetadata(
                display_name="Path Array In",
                type=Field.Kind.ValueType(9),
                repeated=True,
                default_value=[
                    "路径/带有/正斜杠",
                    "路径\\带有\\反斜杠",
                    "路径 带有 '单引号'",
                    '路径 带有 "双引号"',
                    "路径\t带有\t制表符",
                    "路径\n带有\n换行符",
                ],
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Array_In",
                enum_type=None,
            ),
            8: ParameterMetadata(
                display_name="IO In",
                type=Field.Kind.ValueType(9),
                repeated=False,
                default_value="资源",
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
                type=Field.Kind.ValueType(9),
                repeated=True,
                default_value=["资源1", "资源2"],
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
                type=Field.Kind.ValueType(5),
                repeated=False,
                default_value=10,
                annotations={},
                message_type="",
                field_name="Integer_In",
                enum_type=None,
            ),
            11: ParameterMetadata(
                display_name="Enum In",
                type=Field.Kind.ValueType(14),
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
                type=Field.Kind.ValueType(14),
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
        }
        self._output_metadata = {
            1: ParameterMetadata(
                display_name="Float out",
                type=Field.Kind.ValueType(2),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Float_out",
                enum_type=None,
            ),
            2: ParameterMetadata(
                display_name="Double Array out",
                type=Field.Kind.ValueType(1),
                repeated=True,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Double_Array_out",
                enum_type=None,
            ),
            3: ParameterMetadata(
                display_name="Bool out",
                type=Field.Kind.ValueType(8),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Bool_out",
                enum_type=None,
            ),
            4: ParameterMetadata(
                display_name="String out",
                type=Field.Kind.ValueType(9),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="String_out",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="String Array out",
                type=Field.Kind.ValueType(9),
                repeated=True,
                default_value=None,
                annotations={},
                message_type="",
                field_name="String_Array_out",
                enum_type=None,
            ),
            6: ParameterMetadata(
                display_name="Path Out",
                type=Field.Kind.ValueType(9),
                repeated=False,
                default_value=None,
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Out",
                enum_type=None,
            ),
            7: ParameterMetadata(
                display_name="Path Array Out",
                type=Field.Kind.ValueType(9),
                repeated=True,
                default_value=None,
                annotations={"ni/type_specialization": "path"},
                message_type="",
                field_name="Path_Array_Out",
                enum_type=None,
            ),
            8: ParameterMetadata(
                display_name="IO Out",
                type=Field.Kind.ValueType(9),
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
                type=Field.Kind.ValueType(9),
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
                type=Field.Kind.ValueType(5),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="",
                field_name="Integer_Out",
                enum_type=None,
            ),
            11: ParameterMetadata(
                display_name="XY Data Out",
                type=Field.Kind.ValueType(11),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="ni.protobuf.types.DoubleXYData",
                field_name="XY_Data_Out",
                enum_type=None,
            ),
            12: ParameterMetadata(
                display_name="Enum Out",
                type=Field.Kind.ValueType(14),
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
                type=Field.Kind.ValueType(14),
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
                display_name="Double 2D Array out",
                type=Field.Kind.ValueType(11),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="ni.protobuf.types.Double2DArray",
                field_name="Double_2D_Array_out",
                enum_type=None,
            ),
            15: ParameterMetadata(
                display_name="String 2D Array out",
                type=Field.Kind.ValueType(11),
                repeated=False,
                default_value=None,
                annotations={},
                message_type="ni.protobuf.types.String2DArray",
                field_name="String_2D_Array_out",
                enum_type=None,
            ),
        }
        if grpc_channel is not None:
            self._stub = v2_measurement_service_pb2_grpc.MeasurementServiceStub(grpc_channel)
        self._create_file_descriptor()
        self._pin_map_context: PinMapContext = PinMapContext(pin_map_id="", sites=[0])

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
    def sites(self) -> list[int] | None:
        """The sites where the measurement must be executed."""
        return self._pin_map_context.sites

    @sites.setter
    def sites(self, val: list[int]) -> None:
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
                        version=self._version,
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
        self, parameter_values: list[typing.Any]
    ) -> v2_measurement_service_pb2.MeasureRequest:
        serialized_configuration = any_pb2.Any(
            type_url="type.googleapis.com/ni.tests.LocalizedMeasurement_Python.Configurations",
            value=serialize_parameters(
                self._configuration_metadata,
                parameter_values,
                f"{self._service_class}.Configurations",
            ),
        )
        return v2_measurement_service_pb2.MeasureRequest(
            configuration_parameters=serialized_configuration,
            pin_map_context=self._pin_map_context._to_grpc(),
        )

    def _deserialize_response(
        self, response: v2_measurement_service_pb2.MeasureResponse
    ) -> Outputs:
        self._validate_response(response)
        return Outputs._make(
            deserialize_parameters(
                self._output_metadata,
                response.outputs.value,
                f"{self._service_class}.Outputs",
            )
        )

    def _validate_response(self, response: v2_measurement_service_pb2.MeasureResponse) -> None:
        expected_type = "type.googleapis.com/" + "ni.tests.LocalizedMeasurement_Python.Outputs"
        actual_type = response.outputs.type_url
        if actual_type != expected_type:
            warnings.warn(
                f"Wrong message type. Expected {expected_type!r} but got {actual_type!r}",
                WrongMessageTypeWarning,
            )

    def measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: typing.Iterable[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = "示例字符串",
        string_array_in: typing.Iterable[str] = [
            "带有/正斜杠的字符串",
            "带有\\反斜杠的字符串",
            "带有'单引号'的字符串",
            '带有"双引号"的字符串',
            "带有\t制表符的字符串",
            "带有\n换行符的字符串",
        ],
        path_in: pathlib.PurePath = pathlib.PurePath("示例\\路径\\用于\\测试"),
        path_array_in: typing.Iterable[pathlib.PurePath] = [
            pathlib.PurePath("路径/带有/正斜杠"),
            pathlib.PurePath("路径\\带有\\反斜杠"),
            pathlib.PurePath("路径 带有 '单引号'"),
            pathlib.PurePath('路径 带有 "双引号"'),
            pathlib.PurePath("路径\t带有\t制表符"),
            pathlib.PurePath("路径\n带有\n换行符"),
        ],
        io_in: str = "资源",
        io_array_in: typing.Iterable[str] = ["资源1", "资源2"],
        integer_in: int = 10,
        enum_in: EnumInEnum = EnumInEnum.BLUE,
        enum_array_in: typing.Iterable[EnumInEnum] = [EnumInEnum.RED, EnumInEnum.GREEN],
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
        )
        for response in stream_measure_response:
            result = response
        return result

    def stream_measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: typing.Iterable[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string_in: str = "示例字符串",
        string_array_in: typing.Iterable[str] = [
            "带有/正斜杠的字符串",
            "带有\\反斜杠的字符串",
            "带有'单引号'的字符串",
            '带有"双引号"的字符串',
            "带有\t制表符的字符串",
            "带有\n换行符的字符串",
        ],
        path_in: pathlib.PurePath = pathlib.PurePath("示例\\路径\\用于\\测试"),
        path_array_in: typing.Iterable[pathlib.PurePath] = [
            pathlib.PurePath("路径/带有/正斜杠"),
            pathlib.PurePath("路径\\带有\\反斜杠"),
            pathlib.PurePath("路径 带有 '单引号'"),
            pathlib.PurePath('路径 带有 "双引号"'),
            pathlib.PurePath("路径\t带有\t制表符"),
            pathlib.PurePath("路径\n带有\n换行符"),
        ],
        io_in: str = "资源",
        io_array_in: typing.Iterable[str] = ["资源1", "资源2"],
        integer_in: int = 10,
        enum_in: EnumInEnum = EnumInEnum.BLUE,
        enum_array_in: typing.Iterable[EnumInEnum] = [EnumInEnum.RED, EnumInEnum.GREEN],
    ) -> typing.Generator[Outputs]:
        """Perform a streaming measurement.

        Returns:
            Stream of measurement outputs.
        """
        parameter_values = [
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
        ]
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
        self._pin_map_context = self._pin_map_context._replace(pin_map_id=pin_map_id)
