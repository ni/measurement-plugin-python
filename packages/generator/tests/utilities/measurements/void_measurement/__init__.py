"""Contains utility functions to test void measurement service."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import grpc
import ni_measurement_plugin_sdk_service as nims

service_directory = Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "VoidMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("Integer In", nims.DataType.Int32, 10)
def measure(
    integer_input: int,
) -> tuple[()]:
    """Perform a measurement with no output."""
    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    response_interval_in_seconds = 1
    data: list[int] = []

    for index in range(0, integer_input):
        update_time = time.monotonic()
        data.append(index)

        # Delay for the remaining portion of the requested interval and check for cancellation.
        delay = max(0.0, response_interval_in_seconds - (time.monotonic() - update_time))
        if cancellation_event.wait(delay):
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

    return ()
