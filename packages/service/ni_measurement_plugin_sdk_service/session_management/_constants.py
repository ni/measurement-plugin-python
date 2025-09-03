"""Session management constants."""

GRPC_SERVICE_INTERFACE_NAME = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"
GRPC_SERVICE_CLASS = "ni.measurementlink.sessionmanagement.v1.SessionManagementService"


# Constants for instrument_type_id parameters
INSTRUMENT_TYPE_NONE = ""
INSTRUMENT_TYPE_NI_DCPOWER = "niDCPower"
INSTRUMENT_TYPE_NI_HSDIO = "niHSDIO"
INSTRUMENT_TYPE_NI_RFSA = "niRFSA"
INSTRUMENT_TYPE_NI_RFMX = "niRFmx"
INSTRUMENT_TYPE_NI_RFSG = "niRFSG"
INSTRUMENT_TYPE_NI_RFPM = "niRFPM"
INSTRUMENT_TYPE_NI_DMM = "niDMM"
INSTRUMENT_TYPE_NI_DIGITAL_PATTERN = "niDigitalPattern"
INSTRUMENT_TYPE_NI_SCOPE = "niScope"
INSTRUMENT_TYPE_NI_FGEN = "niFGen"
INSTRUMENT_TYPE_NI_DAQMX = "niDAQmx"
INSTRUMENT_TYPE_NI_RELAY_DRIVER = "niRelayDriver"
INSTRUMENT_TYPE_NI_MODEL_BASED_INSTRUMENT = "niModelBasedInstrument"
INSTRUMENT_TYPE_NI_SWITCH_EXECUTIVE_VIRTUAL_DEVICE = "niSwitchExecutiveVirtualDevice"

SITE_SYSTEM_PINS = -1
"""Site number used to identify and filter by system pins.

Pins that have a site number of ``SITE_SYSTEM_PINS`` are system pins and do not
belong to a specific site.

When querying connections, you can specify a site number of ``SITE_SYSTEM_PINS``
to restrict the query to return only system pins.
"""

# Constants for session client details annotations
RESERVED_HOSTNAME = "ni/reserved.hostname"
RESERVED_USERNAME = "ni/reserved.username"
RESERVED_IPADDRESS = "ni/reserved.ipaddress"

REGISTERED_HOSTNAME = "ni/registered.hostname"
REGISTERED_USERNAME = "ni/registered.username"
REGISTERED_IPADDRESS = "ni/registered.ipaddress"
