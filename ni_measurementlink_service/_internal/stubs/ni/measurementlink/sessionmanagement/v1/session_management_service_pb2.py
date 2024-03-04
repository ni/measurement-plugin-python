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


from ni_measurementlink_service._internal.stubs.ni.measurementlink import pin_map_context_pb2 as ni_dot_measurementlink_dot_pin__map__context__pb2
from ni_measurementlink_service._internal.stubs import session_pb2 as session__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\nHni/measurementlink/sessionmanagement/v1/session_management_service.proto\x12\'ni.measurementlink.sessionmanagement.v1\x1a(ni/measurementlink/pin_map_context.proto\x1a\rsession.proto\"\xf1\x01\n\x12SessionInformation\x12\'\n\x07session\x18\x01 \x01(\x0b\x32\x16.nidevice_grpc.Session\x12\x15\n\rresource_name\x18\x02 \x01(\t\x12\x14\n\x0c\x63hannel_list\x18\x03 \x01(\t\x12\x1a\n\x12instrument_type_id\x18\x04 \x01(\t\x12\x16\n\x0esession_exists\x18\x05 \x01(\x08\x12Q\n\x10\x63hannel_mappings\x18\x06 \x03(\x0b\x32\x37.ni.measurementlink.sessionmanagement.v1.ChannelMapping\"\x88\x01\n\x0e\x43hannelMapping\x12\x19\n\x11pin_or_relay_name\x18\x01 \x01(\t\x12\x0c\n\x04site\x18\x02 \x01(\x05\x12\x0f\n\x07\x63hannel\x18\x03 \x01(\t\x12!\n\x19multiplexer_resource_name\x18\x04 \x01(\t\x12\x19\n\x11multiplexer_route\x18\x05 \x01(\t\"\x94\x01\n\x1dMultiplexerSessionInformation\x12\'\n\x07session\x18\x01 \x01(\x0b\x32\x16.nidevice_grpc.Session\x12\x15\n\rresource_name\x18\x02 \x01(\t\x12\x1b\n\x13multiplexer_type_id\x18\x03 \x01(\t\x12\x16\n\x0esession_exists\x18\x04 \x01(\x08\"\xad\x01\n\x16ReserveSessionsRequest\x12:\n\x0fpin_map_context\x18\x01 \x01(\x0b\x32!.ni.measurementlink.PinMapContext\x12\x1a\n\x12pin_or_relay_names\x18\x02 \x03(\t\x12\x1a\n\x12instrument_type_id\x18\x03 \x01(\t\x12\x1f\n\x17timeout_in_milliseconds\x18\x04 \x01(\x05\"\xb0\x03\n\x17ReserveSessionsResponse\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation\x12\x64\n\x14multiplexer_sessions\x18\x02 \x03(\x0b\x32\x46.ni.measurementlink.sessionmanagement.v1.MultiplexerSessionInformation\x12k\n\x0egroup_mappings\x18\x03 \x03(\x0b\x32S.ni.measurementlink.sessionmanagement.v1.ReserveSessionsResponse.GroupMappingsEntry\x1as\n\x12GroupMappingsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12L\n\x05value\x18\x02 \x01(\x0b\x32=.ni.measurementlink.sessionmanagement.v1.ResolvedPinsOrRelays:\x02\x38\x01\"i\n\x18UnreserveSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation\"\x1b\n\x19UnreserveSessionsResponse\"h\n\x17RegisterSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation\"\x1a\n\x18RegisterSessionsResponse\"j\n\x19UnregisterSessionsRequest\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation\"\x1c\n\x1aUnregisterSessionsResponse\"b\n#ReserveAllRegisteredSessionsRequest\x12\x1f\n\x17timeout_in_milliseconds\x18\x01 \x01(\x05\x12\x1a\n\x12instrument_type_id\x18\x02 \x01(\t\"u\n$ReserveAllRegisteredSessionsResponse\x12M\n\x08sessions\x18\x01 \x03(\x0b\x32;.ni.measurementlink.sessionmanagement.v1.SessionInformation\"\x8a\x01\n\"RegisterMultiplexerSessionsRequest\x12\x64\n\x14multiplexer_sessions\x18\x01 \x03(\x0b\x32\x46.ni.measurementlink.sessionmanagement.v1.MultiplexerSessionInformation\"%\n#RegisterMultiplexerSessionsResponse\"\x8c\x01\n$UnregisterMultiplexerSessionsRequest\x12\x64\n\x14multiplexer_sessions\x18\x01 \x03(\x0b\x32\x46.ni.measurementlink.sessionmanagement.v1.MultiplexerSessionInformation\"\'\n%UnregisterMultiplexerSessionsResponse\"x\n\x1dGetMultiplexerSessionsRequest\x12:\n\x0fpin_map_context\x18\x01 \x01(\x0b\x32!.ni.measurementlink.PinMapContext\x12\x1b\n\x13multiplexer_type_id\x18\x02 \x01(\t\"\x86\x01\n\x1eGetMultiplexerSessionsResponse\x12\x64\n\x14multiplexer_sessions\x18\x01 \x03(\x0b\x32\x46.ni.measurementlink.sessionmanagement.v1.MultiplexerSessionInformation\"I\n*GetAllRegisteredMultiplexerSessionsRequest\x12\x1b\n\x13multiplexer_type_id\x18\x01 \x01(\t\"\x93\x01\n+GetAllRegisteredMultiplexerSessionsResponse\x12\x64\n\x14multiplexer_sessions\x18\x01 \x03(\x0b\x32\x46.ni.measurementlink.sessionmanagement.v1.MultiplexerSessionInformation\"2\n\x14ResolvedPinsOrRelays\x12\x1a\n\x12pin_or_relay_names\x18\x01 \x03(\t2\xc1\x0c\n\x18SessionManagementService\x12\x94\x01\n\x0fReserveSessions\x12?.ni.measurementlink.sessionmanagement.v1.ReserveSessionsRequest\x1a@.ni.measurementlink.sessionmanagement.v1.ReserveSessionsResponse\x12\x9a\x01\n\x11UnreserveSessions\x12\x41.ni.measurementlink.sessionmanagement.v1.UnreserveSessionsRequest\x1a\x42.ni.measurementlink.sessionmanagement.v1.UnreserveSessionsResponse\x12\x97\x01\n\x10RegisterSessions\x12@.ni.measurementlink.sessionmanagement.v1.RegisterSessionsRequest\x1a\x41.ni.measurementlink.sessionmanagement.v1.RegisterSessionsResponse\x12\x9d\x01\n\x12UnregisterSessions\x12\x42.ni.measurementlink.sessionmanagement.v1.UnregisterSessionsRequest\x1a\x43.ni.measurementlink.sessionmanagement.v1.UnregisterSessionsResponse\x12\xbb\x01\n\x1cReserveAllRegisteredSessions\x12L.ni.measurementlink.sessionmanagement.v1.ReserveAllRegisteredSessionsRequest\x1aM.ni.measurementlink.sessionmanagement.v1.ReserveAllRegisteredSessionsResponse\x12\xb8\x01\n\x1bRegisterMultiplexerSessions\x12K.ni.measurementlink.sessionmanagement.v1.RegisterMultiplexerSessionsRequest\x1aL.ni.measurementlink.sessionmanagement.v1.RegisterMultiplexerSessionsResponse\x12\xbe\x01\n\x1dUnregisterMultiplexerSessions\x12M.ni.measurementlink.sessionmanagement.v1.UnregisterMultiplexerSessionsRequest\x1aN.ni.measurementlink.sessionmanagement.v1.UnregisterMultiplexerSessionsResponse\x12\xa9\x01\n\x16GetMultiplexerSessions\x12\x46.ni.measurementlink.sessionmanagement.v1.GetMultiplexerSessionsRequest\x1aG.ni.measurementlink.sessionmanagement.v1.GetMultiplexerSessionsResponse\x12\xd0\x01\n#GetAllRegisteredMultiplexerSessions\x12S.ni.measurementlink.sessionmanagement.v1.GetAllRegisteredMultiplexerSessionsRequest\x1aT.ni.measurementlink.sessionmanagement.v1.GetAllRegisteredMultiplexerSessionsResponseB\xf5\x01\n+com.ni.measurementlink.sessionmanagement.v1B\x16SessionManagementProtoP\x01Z\x13sessionmanagementv1\xa2\x02\x04NIMS\xaa\x02\x38NationalInstruments.MeasurementLink.SessionManagement.V1\xca\x02\'NI\\MeasurementLink\\SessionManagement\\V1\xea\x02*NI::MeasurementLink::SessionManagement::V1b\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ni.measurementlink.sessionmanagement.v1.session_management_service_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n+com.ni.measurementlink.sessionmanagement.v1B\026SessionManagementProtoP\001Z\023sessionmanagementv1\242\002\004NIMS\252\0028NationalInstruments.MeasurementLink.SessionManagement.V1\312\002\'NI\\MeasurementLink\\SessionManagement\\V1\352\002*NI::MeasurementLink::SessionManagement::V1'
  _RESERVESESSIONSRESPONSE_GROUPMAPPINGSENTRY._options = None
  _RESERVESESSIONSRESPONSE_GROUPMAPPINGSENTRY._serialized_options = b'8\001'
  _SESSIONINFORMATION._serialized_start=175
  _SESSIONINFORMATION._serialized_end=416
  _CHANNELMAPPING._serialized_start=419
  _CHANNELMAPPING._serialized_end=555
  _MULTIPLEXERSESSIONINFORMATION._serialized_start=558
  _MULTIPLEXERSESSIONINFORMATION._serialized_end=706
  _RESERVESESSIONSREQUEST._serialized_start=709
  _RESERVESESSIONSREQUEST._serialized_end=882
  _RESERVESESSIONSRESPONSE._serialized_start=885
  _RESERVESESSIONSRESPONSE._serialized_end=1317
  _RESERVESESSIONSRESPONSE_GROUPMAPPINGSENTRY._serialized_start=1202
  _RESERVESESSIONSRESPONSE_GROUPMAPPINGSENTRY._serialized_end=1317
  _UNRESERVESESSIONSREQUEST._serialized_start=1319
  _UNRESERVESESSIONSREQUEST._serialized_end=1424
  _UNRESERVESESSIONSRESPONSE._serialized_start=1426
  _UNRESERVESESSIONSRESPONSE._serialized_end=1453
  _REGISTERSESSIONSREQUEST._serialized_start=1455
  _REGISTERSESSIONSREQUEST._serialized_end=1559
  _REGISTERSESSIONSRESPONSE._serialized_start=1561
  _REGISTERSESSIONSRESPONSE._serialized_end=1587
  _UNREGISTERSESSIONSREQUEST._serialized_start=1589
  _UNREGISTERSESSIONSREQUEST._serialized_end=1695
  _UNREGISTERSESSIONSRESPONSE._serialized_start=1697
  _UNREGISTERSESSIONSRESPONSE._serialized_end=1725
  _RESERVEALLREGISTEREDSESSIONSREQUEST._serialized_start=1727
  _RESERVEALLREGISTEREDSESSIONSREQUEST._serialized_end=1825
  _RESERVEALLREGISTEREDSESSIONSRESPONSE._serialized_start=1827
  _RESERVEALLREGISTEREDSESSIONSRESPONSE._serialized_end=1944
  _REGISTERMULTIPLEXERSESSIONSREQUEST._serialized_start=1947
  _REGISTERMULTIPLEXERSESSIONSREQUEST._serialized_end=2085
  _REGISTERMULTIPLEXERSESSIONSRESPONSE._serialized_start=2087
  _REGISTERMULTIPLEXERSESSIONSRESPONSE._serialized_end=2124
  _UNREGISTERMULTIPLEXERSESSIONSREQUEST._serialized_start=2127
  _UNREGISTERMULTIPLEXERSESSIONSREQUEST._serialized_end=2267
  _UNREGISTERMULTIPLEXERSESSIONSRESPONSE._serialized_start=2269
  _UNREGISTERMULTIPLEXERSESSIONSRESPONSE._serialized_end=2308
  _GETMULTIPLEXERSESSIONSREQUEST._serialized_start=2310
  _GETMULTIPLEXERSESSIONSREQUEST._serialized_end=2430
  _GETMULTIPLEXERSESSIONSRESPONSE._serialized_start=2433
  _GETMULTIPLEXERSESSIONSRESPONSE._serialized_end=2567
  _GETALLREGISTEREDMULTIPLEXERSESSIONSREQUEST._serialized_start=2569
  _GETALLREGISTEREDMULTIPLEXERSESSIONSREQUEST._serialized_end=2642
  _GETALLREGISTEREDMULTIPLEXERSESSIONSRESPONSE._serialized_start=2645
  _GETALLREGISTEREDMULTIPLEXERSESSIONSRESPONSE._serialized_end=2792
  _RESOLVEDPINSORRELAYS._serialized_start=2794
  _RESOLVEDPINSORRELAYS._serialized_end=2844
  _SESSIONMANAGEMENTSERVICE._serialized_start=2847
  _SESSIONMANAGEMENTSERVICE._serialized_end=4448
# @@protoc_insertion_point(module_scope)
