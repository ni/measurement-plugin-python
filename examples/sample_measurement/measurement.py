"""Perform a loopback measurement with various data types."""

import logging
import pathlib
import sys
from enum import Enum
from typing import Iterable, Tuple, Generator

import click
import ni_measurementlink_service as nims
from _helpers import configure_logging, verbosity_option
import time

try:
    from _stubs import color_pb2
except ImportError:
    from examples.sample_measurement._stubs import color_pb2  # type: ignore

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "SampleMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory / "SampleMeasurement.measui",
        service_directory / "SampleAllParameters.measui",
        service_directory / "SampleMeasurement.vi",
    ],
)


class Color(Enum):
    """Primary colors used for example enum-typed config and output."""

    NONE = 0
    RED = 1
    GREEN = 2
    BLUE = 3


@measurement_service.register_measurement
@measurement_service.configuration("Int In", nims.DataType.Int64, 10)
@measurement_service.output("Int out", nims.DataType.String)
def measure(
    int_input: int,
) -> Generator[Tuple[str], None, None]:
    """Perform a loopback measurement with various data types."""
    logging.info("Executing measurement")

    def cancel_callback() -> None:
        logging.info("Canceling measurement")

    measurement_service.context.add_cancel_callback(cancel_callback)

    while(int_input > 0):
        time.sleep(1)
        print(int_input)
        int_input = int_input -1
        a = str(int_input)
        print(a)
        yield (a)


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Perform a loopback measurement with various data types."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()
