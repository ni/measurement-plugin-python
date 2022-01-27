""" Metadata for measurement.
"""
# Measurement Metadata
DISPLAY_NAME = "DC Measurement(Py)"
VERSION = "0.0.1"
MEASUREMENT_TYPE = "DC"
PRODUCT_TYPE = "ADC"
SCREEN_FILE_NAME = "DCMeasurementScreen.isscr"

# Measurement Modules and Method Info
MEASUREMENT_MODULE_NAME = "measurement"
MEASUREMENT_METHOD_NAME = "measure"

# Measurement Output Info
MEASUREMENT_OUTPUTS = ["Voltage Measurement", "Output2", "Output3"]

# Instrument Info
RESOURCE_NAME = "DPS_4145"


# Service Info
SERVICE_CLASS = "DCMeasurement_Python"
SERVICE_ID = "{B290B571-CB76-426F-9ACC-5168DC1B027C}"
DESCRIPTION_URL = "https://www.ni.com/measurementservices/dcmeasurement.html"
PROVIDED_SERVICE = "ni.measurements.v1.MeasurementService"
