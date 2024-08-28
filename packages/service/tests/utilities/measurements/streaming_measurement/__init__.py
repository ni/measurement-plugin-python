"""Contains utility functions to test streaming measurement service. """

import pathlib
from typing import Generator, Tuple

import ni_measurement_plugin_sdk_service as nims


service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "streaming_measurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("Integer In", nims.DataType.Int32, 5)
@measurement_service.output("Count Out", nims.DataType.Int32)
@measurement_service.output("Integer Out", nims.DataType.Int32)
def measure(integer_input: int) -> Generator[Tuple[int, int], None, None]:
    """Perform a streaming_measurement with various data types."""
    count = 0
    while count < integer_input:
        count = count + 1
        yield (count, integer_input)
