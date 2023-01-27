"""A default measurement with an array in and out."""
import logging
import pathlib
import sys

import click
import ni_measurementlink_service as nims

parent_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=parent_directory / "example.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[parent_directory / "MeasurementUI.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration("Array in", nims.DataType.DoubleArray1D, [0.0])
@measurement_service.output("Array out", nims.DataType.DoubleArray1D)
def measure(array_input):
    """TODO: replace the following line with your own measurement logic."""
    array_output = array_input
    return (array_output,)


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def main(verbose: int):
    """Host the Sample Measurement service."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
