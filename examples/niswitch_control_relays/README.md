## NI-Switch Control Relays

This is a measurement plug-in example that controls relays using an NI relay driver
(e.g. PXI-2567).

### Features

- Uses the `niswitch` package to access NI-SWITCH from Python
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected
  sites
  - Performs the same operation (open/close relay) on all selected pin/site
    combinations
- Includes InstrumentStudio and Measurement Plug-In UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and
    session registration and unregistration in the `Setup` and `Cleanup`
    sections of the main sequence. For **Test UUTs** and batch process model use
    cases, these steps should be moved to the `ProcessSetup` and
    `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Software

- InstrumentStudio 2025 Q1 or later
- NI-SWITCH
- Recommended: TestStand 2021 SP1 or later

### Required Hardware

This example requires an NI relay driver (e.g. PXI-2567).

By default, this example uses a physical instrument or a simulated instrument
created in NI MAX. To automatically simulate an instrument without using NI MAX,
follow the steps below:
- Create a `.env` file in the measurement service's directory or one of its
  parent directories (such as the root of your Git repository or
  `C:\ProgramData\National Instruments\Plug-Ins\Measurements` for statically
  registered measurement services).
- Add the following options to the `.env` file to enable simulation via the
  driver's `simulate` and `topology` parameters:

  ```
  MEASUREMENT_PLUGIN_NISWITCH_SIMULATE=1
  MEASUREMENT_PLUGIN_NISWITCH_TOPOLOGY=2567/Independent
  ```
