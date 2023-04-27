"""Perform a long running measurement."""
import logging
import pathlib
import random
import time
from typing import Generator, List, Tuple

import click

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "LongRunningMeasurement.serviceconfig",
    version="0.5.0.0",
    ui_file_paths=[service_directory / "LongRunningMeasurement.measui"],
)


Outputs = Tuple[int, str, List[int], float]


@measurement_service.register_measurement
@measurement_service.configuration("time_in_seconds", nims.DataType.Double, 10.0)
@measurement_service.output("random_numbers", nims.DataType.Int32Array1D)
@measurement_service.output("status", nims.DataType.String)
@measurement_service.output("overlimit", nims.DataType.Int32Array1D)
@measurement_service.output("elapsed_time_in_seconds", nims.DataType.Double)
def measure(time_in_seconds: float) -> Generator[Outputs, None, Outputs]:
    """Perform a long running measurement."""
    start_time = time.monotonic()
    status = ""
    random_numbers: List[float] = []
    overlimit: List[float] = []
    elapsed_time_in_seconds = 0.0
    loop_index = 0
    while elapsed_time_in_seconds < time_in_seconds:
        loop_index += 1
        status = f"Loop Index: {loop_index}"
        elapsed_time_in_seconds = time.monotonic() - start_time

        desired_len = int(elapsed_time_in_seconds * 1000.0 / 10.0)
        while len(random_numbers) < desired_len:
            random_numbers.append(random.randint(1, 1000))
            if random_numbers[-1] > 800:
                overlimit.append(random_numbers[-1])

        yield (random_numbers, status, overlimit, elapsed_time_in_seconds)
        time.sleep(10e-3)

    status = "Done."
    return (random_numbers, status, overlimit, elapsed_time_in_seconds)


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def main(verbose: int) -> None:
    """Perform a long running measurement."""
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
