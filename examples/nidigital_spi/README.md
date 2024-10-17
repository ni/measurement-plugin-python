## NI-Digital SPI

This is a measurement plug-in example that tests an SPI device using an NI Digital
Pattern instrument.

### Features

- Uses the `nidigital` package to access the NI-Digital Pattern Driver from
  Python
- Pin-aware, supporting one session, multiple pins, and multiple selected sites
- Includes project files for Digital Pattern Editor, InstrumentStudio,
  Measurement Plug-In UI Editor
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, pre-load files into
  the NI-Digital Pattern Driver, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and
  session registration and unregistration in the `Setup` and `Cleanup` sections
  of the main sequence. For **Test UUTs** and batch process model use cases,
  these steps should be moved to the `ProcessSetup` and `ProcessCleanup`
  callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Software

- InstrumentStudio 2025 Q1 or later
- NI-Digital Pattern Driver
- Recommended: TestStand 2021 SP1 or later

### Required Hardware

This example requires an NI Digital Pattern instrument (e.g. PXIe-6570).

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
  MEASUREMENT_PLUGIN_NIDIGITAL_SIMULATE=1
  MEASUREMENT_PLUGIN_NIDIGITAL_BOARD_TYPE=PXIe
  MEASUREMENT_PLUGIN_NIDIGITAL_MODEL=6570
  ```
