## NI-DAQmx Analog Input Measurement

This is a MeasurementLink example that performs a finite analog input
measurement with NI-DAQmx.

### Features

- Uses the `nidaqmx-python` package to access NI-DAQmx from Python
- Demonstrates how to cancel a running measurement using the driver API's
  asynchronous abort/cancel function
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Not pin-aware
- Does not use the MeasurementLink session management service or NI gRPC Device Server

### Required Driver Software

- NI-DAQmx

### Required Hardware

This example requires a DAQmx device that supports AI voltage measurements (e.g.
PCIe-6363 or other X Series device).