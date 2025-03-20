"""Contains utility functions to test a v2 measurement service that streams data."""

from __future__ import annotations

import pathlib
import threading
import time
from collections.abc import Generator
from typing import List, Tuple

import grpc

import ni_measurement_plugin_sdk_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "StreamingDataMeasurement.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


Outputs = tuple[str, int, list[int]]


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
) -> Generator[Outputs]:
    """Returns the number of responses requested at the requested interval."""
    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    data: list[int] = []

    response_interval_in_seconds = response_interval_in_ms / 1000.0

    for index in range(0, num_responses):
        update_time = time.monotonic()

        if index == error_on_index:
            measurement_service.context.abort(
                grpc.StatusCode.UNKNOWN,
                f"Errored at index {error_on_index}",
            )

        if not cumulative_data:
            data.clear()

        data.extend(index for i in range(data_size))

        yield (name, index, data)

        # Delay for the remaining portion of the requested interval and check for cancellation.
        delay = max(0.0, response_interval_in_seconds - (time.monotonic() - update_time))
        if cancellation_event.wait(delay):
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )
