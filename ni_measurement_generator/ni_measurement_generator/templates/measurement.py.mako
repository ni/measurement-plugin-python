<%page args="display_name, version, measurement_type, product_type, ui_file, ui_file_type, service_class, service_id, description"/>\
\
"""A default measurement with an array in and out."""
import logging
import os
import sys

import click
import ni_measurement_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="${display_name}",
    version="${version}",
    measurement_type="${measurement_type}",
    product_type="${product_type}",
    ui_file_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "${ui_file}"),
    ui_file_type=nims.UIFileType.${ui_file_type},
)

service_info = nims.ServiceInfo(
    service_class="${service_class}",
    service_id="${service_id}",
    description_url="${description}",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)


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

    measurement_service.host_service()
    input("Press enter to close the measurement service.\n")
    measurement_service.close_service()


if __name__ == "__main__":
    main()
    sys.exit(0)
