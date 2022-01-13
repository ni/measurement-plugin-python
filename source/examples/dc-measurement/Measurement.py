"""
Measurement - Can be Edited By User
User can Import driver and 3Party Packages based on requirements
"""

import hightime
import nidcpower

import Metadata

"""
User Measurement API. Returns Voltage Measurement as the only output
"""


def measure(
    voltage_level: float = 0.01,
    current_limit: float = 0.01,
    voltage_level_range: float = 6.0,
    current_limit_range: float = 0.01,
    source_delay: float = 0.0,
) -> float:

    # User Logic :
    timeout = hightime.timedelta(seconds=(source_delay + 1.0))
    with nidcpower.Session(resource_name=Metadata.RESOURCE_NAME) as session:
        # Configure the session.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = voltage_level_range
        session.current_limit_range = current_limit_range
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.voltage_level = voltage_level
        voltages = []
        with session.initiate():
            channel_indices = "0-{0}".format(session.channel_count - 1)
            channels = session.get_channel_names(channel_indices)
            for channel_name in channels:
                print("Channel: {0}".format(channel_name))
                print("---------------------------------")
                print("Voltage 1:")
                measurementValue = session.channels[channel_name].fetch_multiple(
                    count=1, timeout=timeout
                )
                print_fetched_measurements(measurementValue)
                session.output_enabled = False
                print("")
                voltages.append(measurementValue[0].voltage)
    print("Output:", voltages[0])
    return voltages[0] / 10


"""
Utility Method that formats and print the Measured Values
"""


def print_fetched_measurements(measurements):
    print("             Voltage : {:f} V".format(measurements[0].voltage))
    print("              Current: {:f} A".format(measurements[0].current))
    print("        In compliance: {0}".format(measurements[0].in_compliance))
    return None
