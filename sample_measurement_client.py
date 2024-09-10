"""Python Measurement Plug-In Client."""

import json
import logging
import re
import threading
from enum import Enum
from typing import Any, Dict, Generator, List, NamedTuple, Optional, Union

import grpc
from google.protobuf import any_pb2
from google.protobuf import descriptor_pool
from google.protobuf.descriptor_pb2 import FieldDescriptorProto
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
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


class EInEnum(Enum):

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


class ProtobufEnumInEnum(Enum):

    NONE = 0
    PINK = 1
    WHITE = 2
    BLACK = 3


class Output(NamedTuple):
    """Measurement result container."""

    float_out: float
    double_array_out: List[float]
    bool_out: bool
    string_out: str
    enum_out: EInEnum
    protobuf_enum_out: ProtobufEnumInEnum
    string_array_out: List[str]


class SampleMeasurementClient:
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
        self._service_class = "ni.examples.SampleMeasurement_Python"
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
                display_name="String_ In",
                type=9,
                repeated=False,
                default_value="sample string",
                annotations={},
                message_type="",
                field_name="String__In",
                enum_type=None,
            ),
            5: ParameterMetadata(
                display_name="e_! In",
                type=14,
                repeated=False,
                default_value=3,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="e__In",
                enum_type=EInEnum,
            ),
            6: ParameterMetadata(
                display_name="Enum Array In",
                type=14,
                repeated=True,
                default_value=[],
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_Array_In",
                enum_type=EInEnum,
            ),
            7: ParameterMetadata(
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
            8: ParameterMetadata(
                display_name="String Array In",
                type=9,
                repeated=True,
                default_value=["String1", "String2"],
                annotations={},
                message_type="",
                field_name="String_Array_In",
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
                display_name="Enum out",
                type=14,
                repeated=False,
                default_value=None,
                annotations={
                    "ni/enum.values": '{"NONE": 0, "RED": 1, "GREEN": 2, "BLUE": 3}',
                    "ni/type_specialization": "enum",
                },
                message_type="",
                field_name="Enum_out",
                enum_type=EInEnum,
            ),
            6: ParameterMetadata(
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
            7: ParameterMetadata(
                display_name="String Array out",
                type=9,
                repeated=True,
                default_value=None,
                annotations={},
                message_type="",
                field_name="String_Array_out",
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
        enum_values_by_type_name: Dict[str, Dict[str, Any]] = {}
        for configuration in metadata.measurement_signature.configuration_parameters:
            configuration_metadata.append(
                ParameterMetadata.initialize(
                    display_name=configuration.name,
                    type=configuration.type,
                    repeated=configuration.repeated,
                    default_value=None,
                    annotations=dict(configuration.annotations.items()),
                    message_type=configuration.message_type,
                    enum_type=self._get_enum_type(configuration, enum_values_by_type_name),
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
                    enum_type=self._get_enum_type(output, enum_values_by_type_name),
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

    def _get_enum_type(
        self, parameter: Any, enum_values_by_type_name: Dict[str, Dict[str, Any]]
    ) -> Union[Enum, None]:
        enum_type = None
        if parameter.type == FieldDescriptorProto.TYPE_ENUM:
            loaded_enum_values = json.loads(parameter.annotations["ni/enum.values"])
            enum_values_dict = dict((key, value) for key, value in loaded_enum_values.items())

            for existing_enum_name, existing_enum_values in enum_values_by_type_name.items():
                if existing_enum_values == enum_values_dict:
                    return Enum(existing_enum_name, existing_enum_values)
            new_enum_type_name = self._get_enum_class_name(parameter.name)
            enum_values_by_type_name[new_enum_type_name] = enum_values_dict
            enum_type = Enum(new_enum_type_name, enum_values_dict)
        return enum_type

    def _get_enum_class_name(self, name: str) -> str:
        class_name = name.title().replace(" ", "")
        invalid_chars = "`~!@#$%^&*()-+={}[]\|:;',<>.?/ \nr_"
        pattern = f"[{re.escape(invalid_chars)}]"
        class_name = re.sub(pattern, "", class_name)
        return class_name + "Enum"

    def measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string__in: str = "sample string",
        e___in: EInEnum = EInEnum.BLUE,
        enum_array_in: List[EInEnum] = [],
        protobuf_enum_in: ProtobufEnumInEnum = ProtobufEnumInEnum.BLACK,
        string_array_in: List[str] = ["String1", "String2"],
    ) -> Output:
        """Executes the Sample Measurement (Py).

        Returns:
            Measurement output.
        """
        parameter_values = [
            float_in,
            double_array_in,
            bool_in,
            string__in,
            e___in,
            enum_array_in,
            protobuf_enum_in,
            string_array_in,
        ]
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            result = self._deserialize_response(response)
        return result

    def stream_measure(
        self,
        float_in: float = 0.05999999865889549,
        double_array_in: List[float] = [0.1, 0.2, 0.3],
        bool_in: bool = False,
        string__in: str = "sample string",
        e___in: EInEnum = EInEnum.BLUE,
        enum_array_in: List[EInEnum] = [],
        protobuf_enum_in: ProtobufEnumInEnum = ProtobufEnumInEnum.BLACK,
        string_array_in: List[str] = ["String1", "String2"],
    ) -> Generator[Output, None, None]:
        """Executes the Sample Measurement (Py).

        Returns:
            Stream of measurement output.
        """
        parameter_values = [
            float_in,
            double_array_in,
            bool_in,
            string__in,
            e___in,
            enum_array_in,
            protobuf_enum_in,
            string_array_in,
        ]
        request = self._create_measure_request(parameter_values)

        for response in self._get_stub().Measure(request):
            yield self._deserialize_response(response)
