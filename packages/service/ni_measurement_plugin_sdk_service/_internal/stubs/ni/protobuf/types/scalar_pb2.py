# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ni/protobuf/types/scalar.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import attribute_value_pb2 as ni_dot_protobuf_dot_types_dot_attribute__value__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1eni/protobuf/types/scalar.proto\x12\x11ni.protobuf.types\x1a\'ni/protobuf/types/attribute_value.proto\"\x83\x02\n\x06Scalar\x12=\n\nattributes\x18\x01 \x03(\x0b\x32).ni.protobuf.types.Scalar.AttributesEntry\x12\x16\n\x0c\x64ouble_value\x18\x02 \x01(\x01H\x00\x12\x15\n\x0bint32_value\x18\x03 \x01(\x05H\x00\x12\x14\n\nbool_value\x18\x04 \x01(\x08H\x00\x12\x16\n\x0cstring_value\x18\x05 \x01(\tH\x00\x1aT\n\x0f\x41ttributesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x30\n\x05value\x18\x02 \x01(\x0b\x32!.ni.protobuf.types.AttributeValue:\x02\x38\x01\x42\x07\n\x05valueB\x83\x01\n\x15\x63om.ni.protobuf.typesB\x0bScalarProtoP\x01Z\x05types\xa2\x02\x04NIPT\xaa\x02\"NationalInstruments.Protobuf.Types\xca\x02\x11NI\\PROTOBUF\\TYPES\xea\x02\x13NI::Protobuf::Typesb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'ni.protobuf.types.scalar_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\025com.ni.protobuf.typesB\013ScalarProtoP\001Z\005types\242\002\004NIPT\252\002\"NationalInstruments.Protobuf.Types\312\002\021NI\\PROTOBUF\\TYPES\352\002\023NI::Protobuf::Types'
  _SCALAR_ATTRIBUTESENTRY._options = None
  _SCALAR_ATTRIBUTESENTRY._serialized_options = b'8\001'
  _SCALAR._serialized_start=95
  _SCALAR._serialized_end=354
  _SCALAR_ATTRIBUTESENTRY._serialized_start=261
  _SCALAR_ATTRIBUTESENTRY._serialized_end=345
# @@protoc_insertion_point(module_scope)
