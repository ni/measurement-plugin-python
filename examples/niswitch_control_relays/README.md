## NI-Switch Control Relays

This is a MeasurementLink example that controls relays using an NI relay driver
(e.g. PXI-2567).

### Features

- Uses the `niswitch` package to access NI-SWITCH from Python
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected sites
  - Performs the same operation (open/close relay) on all selected pin/site combinations
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence
- Uses the MeasurementLink session management service and NI gRPC Device Server

### Required Driver Software

- NI-SWITCH

### Required Hardware

This example requires an NI relay driver (e.g. PXI-2567).