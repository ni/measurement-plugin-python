## NI-Switch Control Relays

This is a MeasurementLink example that controls relays using an NI relay driver
(e.g. PXI-2567).

### Features

- Uses the `niswitch` package to access NI-SWITCH from Python
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected sites
  - Performs the same operation (open/close relay) on all selected pin/site combinations
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

- NI-SWITCH

### Required Hardware

This example requires an NI relay driver (e.g. PXI-2567).

By default, this example uses a simulated instrument. To use a physical instrument, edit
`measurement.py` and `teststand_fixture.py` to specify `USE_SIMULATION = False`.