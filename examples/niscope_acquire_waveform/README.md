## NI-SCOPE Acquire Waveform

This is a MeasurementLink example that acquires a waveform using an NI oscilloscope.

### Features

- Uses the `niscope` package to access NI-SCOPE from Python
- Demonstrates how to cancel a running measurement while polling measurement status
- Pin-aware, supporting one session, multiple pins, and one selected site
  - Acquires from up to 4 pins
  - Trigger source demonstrates mapping a specific pin to a channel
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence
- Uses the MeasurementLink session management service and NI gRPC Device Server

### Required Driver Software

- NI-SCOPE

### Required Hardware

This example requires an NI oscilloscope (e.g. PXIe-5162 (4CH)).