## NI-SCOPE Acquire Waveform

This is a measurement plug-in example that acquires a waveform using an NI
oscilloscope.

### Features

- Uses the `niscope` package to access NI-SCOPE from Python
- Demonstrates how to cancel a running measurement while polling measurement
  status
- Pin-aware, supporting one session, multiple pins, and one selected site
  - Acquires from up to 4 pins
  - Trigger source demonstrates mapping a specific pin to a channel
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
- NI-SCOPE
- Recommended: TestStand 2021 SP1 or later

### Required Hardware

This example requires an NI oscilloscope (e.g. PXIe-5162 (4CH)).

By default, this example uses a physical instrument or a simulated instrument
created in NI MAX. To automatically simulate an instrument without using NI MAX,
follow the steps below:
- Create a `.env` file in the measurement service's directory or one of its
  parent directories (such as the root of your Git repository or
  `C:\ProgramData\National Instruments\Plug-Ins\Measurements` for statically
  registered measurement services).
- Add the following options to the `.env` file to enable simulation via the
  driver's option string:

  ```
  MEASUREMENT_PLUGIN_NISCOPE_SIMULATE=1
  MEASUREMENT_PLUGIN_NISCOPE_BOARD_TYPE=PXIe
  MEASUREMENT_PLUGIN_NISCOPE_MODEL=5162 (4CH)
  ```
