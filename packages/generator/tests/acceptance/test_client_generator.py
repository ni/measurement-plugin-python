import pathlib
from typing import Generator

import pytest
from ni_measurement_plugin_sdk_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService

from ni_measurement_plugin_sdk_generator.ni_measurement_plugin_client_generator import template
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import test_measurement


def test___command_line_args___create_client___render_without_exception(
    test_assets_directory: pathlib.Path,
    tmp_path_factory: pytest.TempPathFactory,
    stub_v2: v2_measurement_service_pb2_grpc.MeasurementServiceStub,
) -> None:
    temp_directory = tmp_path_factory.mktemp("measurement_plugin_client_files")
    module_name = "test_measurement_client"

    with pytest.raises(SystemExit):
        template.create_client(
            [
                module_name,
                "--measurement-service-class",
                "ni.tests.TestMeasurement_Python",
                "--directory-out",
                temp_directory,
            ]
        )

    golden_path = test_assets_directory / "example_renders" / "measurement_plugin_client"

    filenames = ["measurement_plugin_client.py", "_helpers.py"]
    for filename in filenames:
        _assert_equal(
            golden_path / filename,
            temp_directory / module_name / filename,
        )


def _assert_equal(expected_path: pathlib.Path, result_path: pathlib.Path) -> None:
    expected = expected_path.read_text()
    result = result_path.read_text()

    assert expected == result


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: Generator[DiscoveryServiceProcess, None, None]
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with test_measurement.measurement_service.host_service() as service:
        yield service
