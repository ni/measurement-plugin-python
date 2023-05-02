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

To simulate an NI relay driver in software: open `NI MAX`, right-click `Devices and Interfaces`,
select `Create New...`, and select `Simulated NI-DAQmx Device or Modular Instrument`.
Relay drivers are in the `Switches` category.