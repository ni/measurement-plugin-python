"""Contains utility functions to test that yield and return are supported in measurements."""

from __future__ import annotations

import pathlib
import random
import threading
import time
from collections.abc import Generator
from typing import List

import grpc

import ni_measurement_plugin_sdk_service as nims

RANDOM_NUMBERS_PER_SECOND = 100.0
RANDOM_NUMBER_RANGE = 10.0
UI_UPDATE_INTERVAL_IN_SECONDS = 100e-3

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "UIProgressUpdates.serviceconfig",
    ui_file_paths=[
        service_directory,
    ],
)


Outputs = tuple[float, list[float], str]


@measurement_service.register_measurement
@measurement_service.configuration("time_in_seconds", nims.DataType.Double, 10.0)
@measurement_service.output("elapsed_time_in_seconds", nims.DataType.Double)
@measurement_service.output("random_numbers", nims.DataType.DoubleArray1D)
@measurement_service.output("status", nims.DataType.String)
def measure(time_in_seconds: float) -> Generator[Outputs, None, Outputs]:
    """Generates random numbers and updates the measurement UI to show progress."""
    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    if time_in_seconds < 0.0:
        measurement_service.context.abort(
            grpc.StatusCode.INVALID_ARGUMENT, "time_in_seconds must be non-negative."
        )

    elapsed_time_in_seconds = 0.0
    random_numbers: list[float] = []
    status = ""

    start_time = time.monotonic()
    stop_len = int(time_in_seconds * RANDOM_NUMBERS_PER_SECOND)
    update_number = 1
    while len(random_numbers) < stop_len:
        update_time = time.monotonic()
        elapsed_time_in_seconds = update_time - start_time

        status = f"Update: {update_number}"
        update_number += 1

        desired_len = int(elapsed_time_in_seconds * RANDOM_NUMBERS_PER_SECOND)
        desired_len = max(0, min(desired_len, stop_len))
        random_numbers.extend(_generate_random_numbers(desired_len - len(random_numbers)))

        # Use yield to send incremental updates to an interactive client such as
        # InstrumentStudio.
        yield (elapsed_time_in_seconds, random_numbers, status)

        # Delay for the remaining portion of the UI update interval and check for cancellation.
        delay = max(0.0, UI_UPDATE_INTERVAL_IN_SECONDS - (time.monotonic() - update_time))
        if cancellation_event.wait(delay):
            measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )

    # Non-interactive clients such as TestStand only use the measurement's final
    # update. You may use either yield or return to send the final update.
    status = f"Total updates: {update_number}"
    return (elapsed_time_in_seconds, random_numbers, status)


def _generate_random_numbers(count: int) -> Generator[float]:
    """Generate random numbers between -RANDOM_NUMBER_RANGE and +RANDOM_NUMBER_RANGE."""
    for _ in range(count):
        yield RANDOM_NUMBER_RANGE * (2.0 * random.random() - 1.0)
