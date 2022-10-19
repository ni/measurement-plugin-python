"""A default measurement with an array in and out."""
import contextlib
import json
import logging
import os
import sys

import click
import hightime
import nidcpower

import ni_measurement_service as nims

measurement_info = nims.MeasurementInfo(
    display_name="Pin Centric Measurement",
    version="1.0.0.0",
    measurement_type="MeasurementType",
    product_type="ProductType",
    ui_file_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "PinCentricMeasurement.measui"
    ),
)

service_info = nims.ServiceInfo(
    service_class="Pin Centric Measurement_Python",
    service_id="{B7C55EA2-925B-4246-9088-668EAFD32CFA}",
    description_url="None",
)

measurement_service = nims.MeasurementService(measurement_info, service_info)


@measurement_service.register_measurement
@measurement_service.configuration("Pin Name", nims.DataType.String, "")
@measurement_service.configuration("Options Json", nims.DataType.String, "{}")
@measurement_service.configuration("Voltage Level", nims.DataType.Float, 1.0)
@measurement_service.configuration("Current Limit", nims.DataType.Float, 0.06)
@measurement_service.configuration("Voltage Level Range", nims.DataType.Float, 5.0)
@measurement_service.configuration("Current Limit Range", nims.DataType.Float, 0.06)
@measurement_service.configuration("Source Delay", nims.DataType.Float, 0.05)
@measurement_service.output("Measurements", nims.DataType.String)
def measure(
    pin_name,
    options_json,
    voltage_level,
    current_limit,
    voltage_level_range,
    current_limit_range,
    source_delay,
):
    """Output voltage, waits for source delay, and then takes a measurement."""
    options = json.loads(options_json)
    timeout = hightime.timedelta(seconds=(source_delay + 1.0))
    measurements = []

    with contextlib.ExitStack as stack:
        session_manager = nims.SessionManager()
        session_info = list(
            session_manager.register_sessions(
                pin_names=[pin_name], instrument_type_id="niDCPower", context=nims.PinMapContext()
            )
        )
        stack.callback(session_manager.unreserve_sessions, session_info)

        session = stack.enter_context(
            nidcpower.Session(resource_name=session_info[0].resource_name, options=options)
        )

        # Configure the session.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = voltage_level_range
        session.current_limit_range = current_limit_range
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.voltage_level = voltage_level

        stack.enter_context(session.initiate())

        channel_indices = "0-{0}".format(session.channel_count - 1)
        channels = session.get_channel_names(channel_indices)
        for channel_name in channels:
            measurement = session.channels[channel_name].fetch_multiple(count=1, timeout=timeout)[0]
            session.output_enabled = False
            measurements.append(
                dict(
                    channel_name=channel_name,
                    voltage=measurement.voltage,
                    current=measurement.current,
                    in_compliance=measurement.in_compliance,
                )
            )

    return (json.dumps(measurements),)


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
