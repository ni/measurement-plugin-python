from __future__ import annotations

import importlib.util
import pathlib
from collections.abc import Generator, Sequence
from enum import Enum
from types import ModuleType
from typing import Any

import pytest
from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from tests.conftest import CliRunnerFunction
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import non_streaming_data_measurement


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


def test___measurement_plugin_client___measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        float_out=0.05999999865889549,
        double_array_out=[0.1, 0.2, 0.3],
        bool_out=False,
        string_out="sample string",
        string_array_out=[
            "string with /forwardslash",
            "string with \\backslash",
            "string with 'single quotes'",
            'string with "double quotes"',
            "string with \ttabspace",
            "string with \nnewline",
        ],
        path_out=pathlib.Path("sample\\path\\for\\test"),
        path_array_out=[
            pathlib.Path("path\\with\\forward\\slash"),
            pathlib.Path("path\\with\\backslash"),
            pathlib.Path("path with 'single quotes'"),
            pathlib.Path('path with "double quotes"'),
            pathlib.Path("path\twith\ttabs"),
            pathlib.Path("path\nwith\nnewlines"),
        ],
        io_out="resource",
        io_array_out=["resource1", "resource2"],
        integer_out=10,
        xy_data_out=None,
        enum_out=EnumInEnum.BLUE,
        enum_array_out=[EnumInEnum.RED, EnumInEnum.GREEN],
        protobuf_enum_out=ProtobufEnumInEnum.BLACK,
        double_2d_array_out=array_pb2.Double2DArray(
            rows=2, columns=3, data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ),
        string_2d_array_out=array_pb2.String2DArray(
            rows=2, columns=3, data=["ABC", "DEF", "GHI", "JKL", "MNO", "PQR"]
        ),
    )
    measurement_plugin_client = test_measurement_client_type()

    response = measurement_plugin_client.measure()

    # Enum values are not comparable due to differing imports.
    # So comparing values by converting them to string.
    assert str(response) == str(expected_output)


def test___measurement_plugin_client___measure___converts_output_types(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    response = measurement_plugin_client.measure()

    _verify_output_types(response, measurement_plugin_client_module)


def test___measurement_plugin_client___stream_measure___returns_output(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    expected_output = output_type(
        float_out=0.05999999865889549,
        double_array_out=[0.1, 0.2, 0.3],
        bool_out=False,
        string_out="sample string",
        string_array_out=[
            "string with /forwardslash",
            "string with \\backslash",
            "string with 'single quotes'",
            'string with "double quotes"',
            "string with \ttabspace",
            "string with \nnewline",
        ],
        path_out=pathlib.Path("sample\\path\\for\\test"),
        path_array_out=[
            pathlib.Path("path\\with\\forward\\slash"),
            pathlib.Path("path\\with\\backslash"),
            pathlib.Path("path with 'single quotes'"),
            pathlib.Path('path with "double quotes"'),
            pathlib.Path("path\twith\ttabs"),
            pathlib.Path("path\nwith\nnewlines"),
        ],
        io_out="resource",
        io_array_out=["resource1", "resource2"],
        integer_out=10,
        xy_data_out=None,
        enum_out=EnumInEnum.BLUE,
        enum_array_out=[EnumInEnum.RED, EnumInEnum.GREEN],
        protobuf_enum_out=ProtobufEnumInEnum.BLACK,
        double_2d_array_out=array_pb2.Double2DArray(
            rows=2, columns=3, data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        ),
        string_2d_array_out=array_pb2.String2DArray(
            rows=2, columns=3, data=["ABC", "DEF", "GHI", "JKL", "MNO", "PQR"]
        ),
    )
    measurement_plugin_client = test_measurement_client_type()

    response_iterator = measurement_plugin_client.stream_measure()

    responses = [response for response in response_iterator]
    assert len(responses) == 1
    # Enum values are not comparable due to differing imports.
    # So comparing values by converting them to string.
    assert str(responses[0]) == str(expected_output)


def test___measurement_plugin_client___stream_measure___converts_output_types(
    measurement_plugin_client_module: ModuleType,
) -> None:
    test_measurement_client_type = getattr(measurement_plugin_client_module, "TestMeasurement")
    measurement_plugin_client = test_measurement_client_type()

    response_iterator = measurement_plugin_client.stream_measure()

    responses = [response for response in response_iterator]
    assert len(responses) == 1
    _verify_output_types(responses[0], measurement_plugin_client_module)


@pytest.fixture(scope="module")
def measurement_client_directory(
    create_client: CliRunnerFunction,
    tmp_path_factory: pytest.TempPathFactory,
    measurement_service: MeasurementService,
) -> pathlib.Path:
    """Test fixture that creates a Measurement Plug-In Client."""
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"

    create_client(
        [
            "--measurement-service-class",
            "ni.tests.NonStreamingDataMeasurement_Python",
            "--module-name",
            module_name,
            "--class-name",
            "TestMeasurement",
            "--directory-out",
            str(temp_directory),
        ]
    )

    return temp_directory


@pytest.fixture(scope="module")
def measurement_plugin_client_module(
    measurement_client_directory: pathlib.Path,
) -> ModuleType:
    """Test fixture that imports the generated Measurement Plug-In Client module."""
    module_path = measurement_client_directory / "test_measurement_client.py"
    spec = importlib.util.spec_from_file_location("test_measurement_client.py", module_path)
    if spec is not None:
        imported_module = importlib.util.module_from_spec(spec)
        if spec.loader is not None:
            spec.loader.exec_module(imported_module)
            return imported_module
    pytest.fail("The module specification cannot be None.")


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService]:
    """Test fixture that creates and hosts a Measurement Plug-In Service."""
    with non_streaming_data_measurement.measurement_service.host_service() as service:
        yield service


def _verify_output_types(outputs: Any, measurement_plugin_client_module: ModuleType) -> None:
    output_type = getattr(measurement_plugin_client_module, "Outputs")
    enum_type = getattr(measurement_plugin_client_module, "EnumInEnum")
    protobuf_enum_type = getattr(measurement_plugin_client_module, "ProtobufEnumInEnum")

    _assert_type(outputs, output_type)
    _assert_type(outputs.float_out, float)
    _assert_collection_type(outputs.double_array_out, Sequence, float)
    _assert_type(outputs.bool_out, bool)
    _assert_type(outputs.string_out, str)
    _assert_collection_type(outputs.string_array_out, Sequence, str)
    _assert_type(outputs.path_out, pathlib.Path)
    _assert_collection_type(outputs.path_array_out, Sequence, pathlib.Path)
    _assert_type(outputs.io_out, str)
    _assert_collection_type(outputs.io_array_out, Sequence, str)
    _assert_type(outputs.integer_out, int)
    _assert_type(outputs.xy_data_out, type(None))
    _assert_type(outputs.io_out, str)
    _assert_collection_type(outputs.io_array_out, Sequence, str)
    _assert_type(outputs.enum_out, enum_type)
    _assert_collection_type(outputs.enum_array_out, Sequence, enum_type)
    _assert_type(outputs.protobuf_enum_out, protobuf_enum_type)
    _assert_type(outputs.double_2d_array_out, array_pb2.Double2DArray)
    _assert_type(outputs.string_2d_array_out, array_pb2.String2DArray)


def _assert_type(value: Any, expected_type: type[Any] | tuple[type[Any], ...]) -> None:
    assert isinstance(
        value, expected_type
    ), f"{value!r} has type {type(value)}, expected {expected_type}"


def _assert_collection_type(
    value: Any,
    expected_type: type[Any] | tuple[type[Any], ...],
    expected_element_type: type[Any] | tuple[type[Any], ...],
) -> None:
    _assert_type(value, expected_type)
    for element in value:
        _assert_type(element, expected_element_type)
