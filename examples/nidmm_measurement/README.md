## NI-DMM Measurement

This is a MeasurementLink example that performs a measurement using an NI DMM.

### Features

- Uses the `nidmm` package to access NI-DMM from Python
- Pin-aware, supporting one session, one pin, and one selected site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence
- Uses the MeasurementLink session management service and NI gRPC Device Server

### Required Driver Software

- NI-DMM

### Required Hardware

This example requires an NI DMM (e.g. PXI-4072).