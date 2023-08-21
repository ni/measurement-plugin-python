## NI-DMM Measurement

This is a MeasurementLink example that performs a measurement using an NI DMM.

### Features

- Uses the `nidmm` package to access NI-DMM from Python
- Pin-aware, supporting one session, one pin, and one selected site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-DMM

### Required Hardware

This example requires an NI DMM (e.g. PXIe-4081).

By default, this example uses a simulated instrument. To use a physical instrument, edit
`_constants.py` to specify `USE_SIMULATION = False`.
