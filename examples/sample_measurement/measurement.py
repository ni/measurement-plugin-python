"""User Measurement.

User can Import driver and 3Party Packages based on requirements.

"""
import logging
import pathlib
import sys

import click

import ni_measurement_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="SampleMeasurement",
    version="0.1.0.0",
    measurement_type="Sample",
    product_type="Sample",
    ui_file_paths=[
        pathlib.Path(__file__).resolve().parent / "SampleMeasurement.measui",
        pathlib.Path(__file__).resolve().parent / "SampleAllParameters.measui",
    ],
)

service_info = nims.ServiceInfo(
    service_class="ni.examples.SampleMeasurement_Python",
    description_url="https://www.ni.com/measurementservices/samplemeasurement.html",
)

sample_measurement_service = nims.MeasurementService(measurement_info, service_info)


@sample_measurement_service.register_measurement
@sample_measurement_service.configuration("Float In", nims.DataType.Float, 0.06)
@sample_measurement_service.configuration(
    "Double Array In", nims.DataType.DoubleArray1D, [0.1, 0.2, 0.3]
)
@sample_measurement_service.configuration("Bool In", nims.DataType.Boolean, False)
@sample_measurement_service.configuration("String In", nims.DataType.String, "sample string")
@sample_measurement_service.output("Float out", nims.DataType.Float)
@sample_measurement_service.output("Double Array out", nims.DataType.DoubleArray1D)
@sample_measurement_service.output("Bool out", nims.DataType.Boolean)
@sample_measurement_service.output("String out", nims.DataType.String)
def measure(float_input, double_array_input, bool_input, string_input):
    """User Measurement."""
    # User Logic :
    print("Executing SampleMeasurement(Py)")

    def cancel_callback():
        print("Canceling SampleMeasurement(Py)")

    sample_measurement_service.context.add_cancel_callback(cancel_callback)

    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input

    return (float_output, float_array_output, bool_output, string_output)


@click.command
@click.option(
    "-v", "--verbose", count=True, help="Enable verbose logging. Repeat to increase verbosity."
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

    sample_measurement_service.host_service()
    input("Press enter to close the measurement service.\n")
    sample_measurement_service.close_service()


if __name__ == "__main__":
    sys.exit(main())
