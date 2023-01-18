## NI-DCPower Source DC Voltage

This is a MeasurementLink example that sources and measures a DC voltage with an NI SMU.

### Features

- Uses the `nidcpower` package to access NI-DCPower from Python
- Demonstrates how to cancel a running measurement by breaking a long wait into
  multiple short waits
- Pin-aware, supporting one session and multiple pins
  - Sources the same DC voltage level on all selected pin/site combinations
  - Measures the DC voltage and current for each selected pin/site combination
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-DCPower

### Required Hardware

This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141).