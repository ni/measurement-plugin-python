## NI-FGEN Standard Function

This is a measurement plug-in example that generates a standard function waveform
using an NI waveform generator.

### Features

- Uses the `nifgen` package to access NI-FGEN from Python
- Demonstrates how to cancel a running measurement by breaking a long wait into
  multiple short waits
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected
  sites
  - Outputs the same waveform configuration on all selected pin/site
    combinations
  - Does not synchronize waveforms
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
- NI-FGEN
- Recommended: TestStand 2021 SP1 or later

### Required Hardware

This example requires an NI waveform generator (e.g. PXIe-5423 (2CH)).

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
  MEASUREMENT_PLUGIN_NIFGEN_SIMULATE=1
  MEASUREMENT_PLUGIN_NIFGEN_BOARD_TYPE=PXIe
  MEASUREMENT_PLUGIN_NIFGEN_MODEL=5423 (2CH)
  ```
