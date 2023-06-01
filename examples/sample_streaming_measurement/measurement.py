"""Returns the number of responses requested at the requested interval."""
import logging
import pathlib
import threading
import time
from typing import Generator, List, Tuple

import click
import grpc

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "SampleStreamingMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[service_directory / "SampleStreamingMeasurement.measui"],
)


Outputs = Tuple[str, int, List[int]]


@measurement_service.register_measurement
@measurement_service.configuration("name", nims.DataType.String, "<Name>")
@measurement_service.configuration("num_responses", nims.DataType.Int32, 10)
@measurement_service.configuration("data_size", nims.DataType.Int32, 1)
@measurement_service.configuration("cumulative_data", nims.DataType.Boolean, True)
@measurement_service.configuration("response_interval_in_ms", nims.DataType.Int32, 1000)
@measurement_service.configuration("error_on_index", nims.DataType.Int32, -1)
@measurement_service.output("name", nims.DataType.String)
@measurement_service.output("index", nims.DataType.Int32)
@measurement_service.output("data", nims.DataType.Int32Array1D)
def measure(
    name: str,
    num_responses: int,
    data_size: int,
    cumulative_data: bool,
    response_interval_in_ms: int,
    error_on_index: int,
) -> Generator[Outputs, None, Outputs]:
    """
    Returns the number of responses requested at the requested interval. Each response contains a name, index, and data which is populated based on the
    data size requested and whether or not cumulative data has been requested. This measurement will error at the requested error index if greater than -1.
    """
    logging.info("Executing measurement")
    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    data: List[int] = []

    start_time = time.monotonic()
    response_interval_in_seconds = response_interval_in_ms / 1000.0
    update_number = 1
    index = 0

    for index in range(0, num_responses):
        update_time = time.monotonic()

        if index == error_on_index:
            measurement_service.context.abort(
                grpc.StatusCode.UNKNOWN,
                f"Errored at requested index: {error_on_index}",
            )

        if not cumulative_data:
            data.clear()

        data.extend(index for i in range(data_size))

        yield (name, index, data)

        # Delay for the remaining portion of the requested response interval and check for cancellation.
        delay = max(0.0, response_interval_in_seconds - (time.monotonic() - update_time))
        if cancellation_event.wait(delay):
            logging.info("Canceling measurement")
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

    logging.info("Completed measurement")


@click.command
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def main(verbosity: int) -> None:
    """Returns the number of responses requested at the requested interval."""
    _configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


def _configure_logging(verbosity: int):
    """Configure logging for this process."""
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)


if __name__ == "__main__":
    main()
