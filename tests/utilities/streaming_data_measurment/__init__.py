"""Contains Test Doubles - Returns the number of responses requested at the requested interval."""
import pathlib
import threading
import time
from typing import Generator, List, Tuple

import grpc

import ni_measurementlink_service as nims

service_directory = pathlib.Path(__file__).resolve().parent.parent.parent
fake_streaming_data_measurement_service = nims.MeasurementService(
    service_config_path=service_directory
    / "examples/sample_streaming_measurement/SampleStreamingMeasurement.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory
        / "examples/sample_streaming_measurement/SampleStreamingMeasurement.measui"
    ],
)


Outputs = Tuple[str, int, List[int]]


@fake_streaming_data_measurement_service.register_measurement
@fake_streaming_data_measurement_service.configuration("name", nims.DataType.String, "<Name>")
@fake_streaming_data_measurement_service.configuration("num_responses", nims.DataType.Int32, 10)
@fake_streaming_data_measurement_service.configuration("data_size", nims.DataType.Int32, 1)
@fake_streaming_data_measurement_service.configuration(
    "cumulative_data", nims.DataType.Boolean, True
)
@fake_streaming_data_measurement_service.configuration(
    "response_interval_in_ms", nims.DataType.Int32, 1000
)
@fake_streaming_data_measurement_service.configuration("error_on_index", nims.DataType.Int32, -1)
@fake_streaming_data_measurement_service.output("name", nims.DataType.String)
@fake_streaming_data_measurement_service.output("index", nims.DataType.Int32)
@fake_streaming_data_measurement_service.output("data", nims.DataType.Int32Array1D)
def measure(
    name: str,
    num_responses: int,
    data_size: int,
    cumulative_data: bool,
    response_interval_in_ms: int,
    error_on_index: int,
) -> Generator[Outputs, None, None]:
    """Returns the number of responses requested at the requested interval."""
    cancellation_event = threading.Event()
    fake_streaming_data_measurement_service.context.add_cancel_callback(cancellation_event.set)

    data: List[int] = []

    response_interval_in_seconds = response_interval_in_ms / 1000.0

    for index in range(0, num_responses):
        update_time = time.monotonic()

        if index == error_on_index:
            fake_streaming_data_measurement_service.context.abort(
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
            fake_streaming_data_measurement_service.context.abort(
                grpc.StatusCode.CANCELLED, "Client requested cancellation."
            )
