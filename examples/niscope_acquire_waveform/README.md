## NI-SCOPE Acquire Waveform

This is a MeasurementLink example that acquires a waveform using an NI oscilloscope.

### Features

- Uses the `niscope` package to access NI-SCOPE from Python
- Demonstrates how to cancel a running measurement while polling measurement status
- Pin-aware, supporting one session, multiple pins, and one selected site
  - Acquires from up to 4 pins
  - Trigger source demonstrates mapping a specific pin to a channel
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-SCOPE

### Required Hardware

This example requires an NI oscilloscope (e.g. PXIe-5162 (4CH)).

To simulate an NI oscilloscope in software: open `NI MAX`, right-click `Devices and Interfaces`,
select `Create New...`, and select `Simulated NI-DAQmx Device or Modular Instrument`.
Oscilloscopes are in the `High Speed Digitizers` category.