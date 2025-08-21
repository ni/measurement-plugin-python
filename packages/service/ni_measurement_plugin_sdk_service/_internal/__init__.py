"""Internal modules and classes for Measurement Framework."""

import sys

import ni.protobuf


# Redirect old imports of the stubs that used to be defined here to their new location.
sys.modules["ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf"] = ni.protobuf
