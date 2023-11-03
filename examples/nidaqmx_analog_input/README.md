## NI-DAQmx Analog Input Measurement

This is a MeasurementLink example that performs a finite analog input
measurement with NI-DAQmx.

### Features

- Uses the `nidaqmx-python` package to access NI-DAQmx from Python
- Pin-aware, supporting one session, one pin, and one selected site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other measurement
  services when running measurements from TestStand.

> **Note**
>
> Running this measurement requires MeasurementLink 2023 Q3 or later.

### Required Driver Software

- NI-DAQmx

### Required Hardware

This example requires a DAQmx device that supports AI voltage measurements (e.g.
PCIe-6363 or other X Series device).

To simulate a DAQmx device in software: open `NI MAX`, right-click `Devices and Interfaces`,
select `Create New...`, and select `Simulated NI-DAQmx Device or Modular Instrument`.