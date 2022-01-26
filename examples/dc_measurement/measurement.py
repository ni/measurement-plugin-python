"""
Measurement - Can be Edited By User
User can Import driver and 3Party Packages based on requirements
"""

import hightime
import nidcpower

import metadata

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
    print("Executing DCMeasurement(Py)")
    timeout = hightime.timedelta(seconds=(source_delay + 1.0))
    with nidcpower.Session(resource_name=metadata.RESOURCE_NAME) as session:
        # Configure the session.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = current_limit
        session.voltage_level_range = voltage_level_range
        session.current_limit_range = current_limit_range
        session.source_delay = hightime.timedelta(seconds=source_delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.voltage_level = voltage_level
        measured_value = None
        with session.initiate():
            channel = session.get_channel_names("0")
            measured_value = session.channels[channel].fetch_multiple(count=1, timeout=timeout)
    print_fetched_measurements(measured_value)
    output_value = measured_value[0].voltage / 10
    print("Output Value:", output_value)
    print("---------------------------------")
    return output_value


"""
Utility Method that formats and print the Measured Values
"""


def print_fetched_measurements(measurements):
    layout = "{: >20} : {:f}{}"
    print("Fetched Measurement Values:")
    print(layout.format("Voltage", measurements[0].voltage, " V"))
    print(layout.format("Current", measurements[0].current, " A"))
    print(layout.format("In compliance", measurements[0].in_compliance, ""))
    return None
