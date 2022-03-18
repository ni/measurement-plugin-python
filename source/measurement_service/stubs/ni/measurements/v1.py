# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: Measurement.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import List, Optional

import betterproto
import grpclib

from .google import protobuf
from .google.protobuf import Field


@dataclass
class GetMetadataRequest(betterproto.Message):
    """
    Below message is the metadata request which is currently empty Can add any
    fields in future as required
    """

    pass


@dataclass
class MeasurementDetails(betterproto.Message):
    """
    Contains measurement details Other details can be added in future as
    required
    """

    # Measurement Display name for client to display to user
    display_name: str = betterproto.string_field(1)
    # Measurement version that helps to maintain versions of a measurement in
    # future
    version: str = betterproto.string_field(2)
    # Represents category of measurement for the ProductType(example: AC or DC
    # measurements) Helps to provide better UI experience(example: filter using
    # measurement_type)
    measurement_type: str = betterproto.string_field(3)
    # Represents type of the DUT(example: ADC, LDO,...) Helps to provide better
    # UI experience(example: filter using product_type)
    product_type: str = betterproto.string_field(4)


@dataclass
class MeasurementParameters(betterproto.Message):
    """Contains measurement parameters details"""

    # Configuration Message's Packagename.MessageName This is used by client to
    # set Any Typeurl
    configuration_parameters_messagetype: str = betterproto.string_field(1)
    # Measurement configuration parameters details Helps client to form request
    # with configurations for executing measurement
    configuration_parameters: List[
        "ConfigurationParameter"
    ] = betterproto.message_field(2)
    # Parameter default values Can be used to show the default value in the UI
    # for a bound element
    configuration_defaults: protobuf.Any = betterproto.message_field(3)
    # Output Message's Packagename.MessageName. This is used by client to set Any
    # Typeurl
    outputs_message_type: str = betterproto.string_field(4)
    # Measurement output details Helps client to de-serialize measurement
    # response after executing measurement
    outputs: List["Output"] = betterproto.message_field(5)


@dataclass
class UserInterfaceDetails(betterproto.Message):
    """
    Contains measurement User Interface details - other details can be added in
    future as required
    """

    # Measurement configuration UI URL Helps client to load UI URL for user
    # interactions
    configuration_ui_url: str = betterproto.string_field(1)


@dataclass
class GetMetadataResponse(betterproto.Message):
    """
    Contains all metadata related to measurement(Basic, Parameter and
    UserInterface)
    """

    # Measurement details
    measurement_details: "MeasurementDetails" = betterproto.message_field(1)
    # Measurement Configurations and outputs details
    measurement_parameters: "MeasurementParameters" = betterproto.message_field(2)
    # Measurement User Interface details
    user_interface_details: "UserInterfaceDetails" = betterproto.message_field(3)


@dataclass
class ConfigurationParameter(betterproto.Message):
    """measurement configuration info that is part of metadata"""

    # Represents order of parameter Used for gRPC message serialization This
    # allows measurement services to use the gRPC approach for backwards
    # compatibility
    protobuf_id: int = betterproto.uint32_field(1)
    # Datatype of the parameter Helps to de-serialize data into appropriate type
    type: Field.Kind = betterproto.enum_field(2)
    # Parameter name Helps to bind UI elements with configurations
    name: str = betterproto.string_field(3)
    # Represents if the value is repeated
    repeated: bool = betterproto.bool_field(4)


@dataclass
class Output(betterproto.Message):
    """measurement output info that is part of metadata"""

    # Represents order of outputs Used for gRPC message serialization This allows
    # measurement services to use the gRPC approach for backwards compatibility
    protobuf_id: int = betterproto.uint32_field(1)
    # Datatype of the output Helps to de-serialize data into appropriate type
    type: Field.Kind = betterproto.enum_field(2)
    # output name Helps to bind UI elements with outputs
    name: str = betterproto.string_field(3)
    # Represents if the value is repeated
    repeated: bool = betterproto.bool_field(4)


@dataclass
class MeasureRequest(betterproto.Message):
    """message that holds measurement configurations at run time"""

    configuration_parameters: protobuf.Any = betterproto.message_field(1)


@dataclass
class MeasureResponse(betterproto.Message):
    """message that holds measurement outputs at run time"""

    outputs: protobuf.Any = betterproto.message_field(1)


class MeasurementServiceStub(betterproto.ServiceStub):
    """Service that contains methods related to measurement"""

    async def get_metadata(self) -> GetMetadataResponse:
        """API to get complete metadata"""

        request = GetMetadataRequest()

        return await self._unary_unary(
            "/ni.measurements.v1.MeasurementService/GetMetadata",
            request,
            GetMetadataResponse,
        )

    async def measure(
        self, *, configuration_parameters: Optional[protobuf.Any] = None
    ) -> MeasureResponse:
        """API to measure"""

        request = MeasureRequest()
        if configuration_parameters is not None:
            request.configuration_parameters = configuration_parameters

        return await self._unary_unary(
            "/ni.measurements.v1.MeasurementService/Measure",
            request,
            MeasureResponse,
        )
