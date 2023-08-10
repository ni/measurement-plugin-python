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
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should 
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-SCOPE

### Required Hardware

This example requires an NI oscilloscope (e.g. PXIe-5162 (4CH)).

By default, this example uses a simulated instrument. To use a physical instrument, edit
`_niscope_helpers.py` and `teststand_fixture.py` to specify `USE_SIMULATION = False`.