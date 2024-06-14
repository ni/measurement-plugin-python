"""Contains utility functions to test loopback measurement service. """

import pathlib

import ni_measurement_plugin_sdk_service as nims

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "v1_only.serviceconfig",
    version="0.1.0.0",
    ui_file_paths=[
        service_directory,
    ],
)


@measurement_service.register_measurement
@measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@measurement_service.output("Float out", nims.DataType.Float)
def measure(float_input):
    """Loopback measurement on the float input."""
    float_output = float_input

    return float_output
