# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ni/measurementlink/sessionmanagement/v1/session_management_service.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ni_measurement_service._internal.stubs.ni.measurementlink import (
    pin_map_context_pb2 as ni_dot_measurementlink_dot_pin__map__context__pb2,
)
from ni_measurement_service._internal.stubs.nidevice_grpc import (
    session_pb2 as nidevice__grpc_dot_session__pb2,
)


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\nHni/measurementlink/sessionmanagement/v1/session_management_service.proto\x12\'ni.measurementlink.sessionmanagement.v1\x1a(ni/measurementlink/pin_map_context.proto\x1a\x1bnidevice_grpc/session.proto"\xf1\x01\n\x12SessionInformation\x12\'\n\x07session\x18\x01 \x01(\x0b\x32\x16.nidevice_grpc.Session\x12\x15\n\rresource_name\x18\x02 \x01(\t\x12\x14\n\x0c\x63hannel_list\x18\x03 \x01(\t\x12\x1a\n\x12instrument_type_id\x18\x04 \x01(\t\x12\x16\n\x0esession_exists\x18\x05 \x01(\x08\x12Q\n\x10\x63hannel_mappings\x18\x06 \x03(\x0b\x32\x37.ni.measurementlink.sessionmanagement.v1.ChannelMapping"J\n\x0e\x43hannelMapping\x12\x19\n\x11pin_or_relay_name\x18\x01 \x01(\t\x12\x0c\n\x04site\x18\x02 \x01(\x05\x12\x0f\n\x07\x63hannel\x18\x03 \x01(\t"\xad\x01\n\x16ReserveSessionsRequest\x12:\n\x0fpin_map_context\x18\x01 \x01(\x0b\x32!.ni.measurementlink.PinMapContext\x12\x1a\n\x12pin_or_relay_names\x18\x02 \x03(\t\x12\x1a\n\x12instrument_type_id\x18\x03 \x01(\t\x12\x1f\n\x17timeout_in_milliseconds\x18\x04 \x01(\x05"h\n\x17ReserveSessionsResponse\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation"i\n\x18UnreserveSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation"\x1b\n\x19UnreserveSessionsResponse"h\n\x17RegisterSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation"\x1a\n\x18RegisterSessionsResponse"j\n\x19UnregisterSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation"\x1c\n\x1aUnregisterSessionsResponse"b\n#ReserveAllRegisteredSessionsRequest\x12\x1f\n\x17timeout_in_milliseconds\x18\x01 \x01(\x05\x12\x1a\n\x12instrument_type_id\x18\x02 \x01(\t"u\n$ReserveAllRegisteredSessionsResponse\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation2\xc6\x06\n\x18SessionManagementService\x12\x94\x01\n\x0fReserveSessions\x12?.ni.measurementlink.sessionmanagement.v1.ReserveSessionsRequest\x1a@.ni.measurementlink.sessionmanagement.v1.ReserveSessionsResponse\x12\x9a\x01\n\x11UnreserveSessions\x12\x41.ni.measurementlink.sessionmanagement.v1.UnreserveSessionsRequest\x1a\x42.ni.measurementlink.sessionmanagement.v1.UnreserveSessionsResponse\x12\x97\x01\n\x10RegisterSessions\x12@.ni.measurementlink.sessionmanagement.v1.RegisterSessionsRequest\x1a\x41.ni.measurementlink.sessionmanagement.v1.RegisterSessionsResponse\x12\x9d\x01\n\x12UnregisterSessions\x12\x42.ni.measurementlink.sessionmanagement.v1.UnregisterSessionsRequest\x1a\x43.ni.measurementlink.sessionmanagement.v1.UnregisterSessionsResponse\x12\xbb\x01\n\x1cReserveAllRegisteredSessions\x12L.ni.measurementlink.sessionmanagement.v1.ReserveAllRegisteredSessionsRequest\x1aM.ni.measurementlink.sessionmanagement.v1.ReserveAllRegisteredSessionsResponseB\xf5\x01\n+com.ni.measurementlink.sessionmanagement.v1B\x16SessionManagementProtoP\x01Z\x13sessionmanagementv1\xa2\x02\x04NIMS\xaa\x02\x38NationalInstruments.MeasurementLink.SessionManagement.V1\xca\x02\'NI\\MeasurementLink\\SessionManagement\\V1\xea\x02*NI::MeasurementLink::SessionManagement::V1b\x06proto3'
)

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(
    DESCRIPTOR, "ni.measurementlink.sessionmanagement.v1.session_management_service_pb2", globals()
)
if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    DESCRIPTOR._serialized_options = b"\n+com.ni.measurementlink.sessionmanagement.v1B\026SessionManagementProtoP\001Z\023sessionmanagementv1\242\002\004NIMS\252\0028NationalInstruments.MeasurementLink.SessionManagement.V1\312\002'NI\\MeasurementLink\\SessionManagement\\V1\352\002*NI::MeasurementLink::SessionManagement::V1"
    _SESSIONINFORMATION._serialized_start = 189
    _SESSIONINFORMATION._serialized_end = 430
    _CHANNELMAPPING._serialized_start = 432
    _CHANNELMAPPING._serialized_end = 506
    _RESERVESESSIONSREQUEST._serialized_start = 509
    _RESERVESESSIONSREQUEST._serialized_end = 682
    _RESERVESESSIONSRESPONSE._serialized_start = 684
    _RESERVESESSIONSRESPONSE._serialized_end = 788
    _UNRESERVESESSIONSREQUEST._serialized_start = 790
    _UNRESERVESESSIONSREQUEST._serialized_end = 895
    _UNRESERVESESSIONSRESPONSE._serialized_start = 897
    _UNRESERVESESSIONSRESPONSE._serialized_end = 924
    _REGISTERSESSIONSREQUEST._serialized_start = 926
    _REGISTERSESSIONSREQUEST._serialized_end = 1030
    _REGISTERSESSIONSRESPONSE._serialized_start = 1032
    _REGISTERSESSIONSRESPONSE._serialized_end = 1058
    _UNREGISTERSESSIONSREQUEST._serialized_start = 1060
    _UNREGISTERSESSIONSREQUEST._serialized_end = 1166
    _UNREGISTERSESSIONSRESPONSE._serialized_start = 1168
    _UNREGISTERSESSIONSRESPONSE._serialized_end = 1196
    _RESERVEALLREGISTEREDSESSIONSREQUEST._serialized_start = 1198
    _RESERVEALLREGISTEREDSESSIONSREQUEST._serialized_end = 1296
    _RESERVEALLREGISTEREDSESSIONSRESPONSE._serialized_start = 1298
    _RESERVEALLREGISTEREDSESSIONSRESPONSE._serialized_end = 1415
    _SESSIONMANAGEMENTSERVICE._serialized_start = 1418
    _SESSIONMANAGEMENTSERVICE._serialized_end = 2256
# @@protoc_insertion_point(module_scope)
