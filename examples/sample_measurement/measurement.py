"""User Measurement.

User can Import driver and 3Party Packages based on requirements.

"""
import os

from ni_measurement_service.measurement.info import DataType
from ni_measurement_service.measurement.info import MeasurementInfo
from ni_measurement_service.measurement.info import ServiceInfo
from ni_measurement_service.measurement.info import UIFileType
from ni_measurement_service.measurement.service import MeasurementService

measurement_info = MeasurementInfo(
    display_name="SampleMeasurement",
    version="0.1.0.0",
    measurement_type="Sample",
    product_type="Sample",
    ui_file_path=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "SampleMeasurementScreen.isscr"
    ),
    ui_file_type=UIFileType.ScreenFile,
)

service_info = ServiceInfo(
    service_class="SampleMeasurement_Python",
    service_id="{E0095551-CB4B-4352-B65B-4280973694B2}",
    description_url="https://www.ni.com/measurementservices/samplemeasurement.html",
)

sample_measurement_service = MeasurementService(measurement_info, service_info)


@sample_measurement_service.register_measurement
@sample_measurement_service.configuration("Float In", DataType.Float, 0.06)
@sample_measurement_service.configuration(
    "Double Array In", DataType.DoubleArray1D, [0.1, 0.2, 0.3]
)
@sample_measurement_service.configuration("Bool In", DataType.Boolean, False)
@sample_measurement_service.configuration("String In", DataType.String, "sample string")
@sample_measurement_service.output("Float out", DataType.Float)
@sample_measurement_service.output("Double Array out", DataType.DoubleArray1D)
@sample_measurement_service.output("Bool out", DataType.Boolean)
@sample_measurement_service.output("String out", DataType.String)
def measure(float_input, double_array_input, bool_input, string_input):
    """User Measurement."""
    # User Logic :
    float_output = float_input
    float_array_output = double_array_input
    bool_output = bool_input
    string_output = string_input

    return [float_output, float_array_output, bool_output, string_output]


"""Driver Method.
"""
if __name__ == "__main__":
    sample_measurement_service.host_as_grpc_service()
    input("To Exit during the Service lifetime, Press Enter.\n")
    sample_measurement_service.close_service()
