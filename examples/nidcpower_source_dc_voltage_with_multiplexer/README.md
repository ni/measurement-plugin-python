## NI-DCPower Source DC Voltage

This is a MeasurementLink example that sources and measures a DC voltage with an
NI SMU via an NI-SWITCH multiplexer.

### Features

- Uses the `nidcpower` package to access NI-DCPower from Python
- Uses the `niswitch` package to access NI-SWITCH from Python
- Includes InstrumentStudio and MeasurementLink UI Editor project files
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

- MeasurementLink 2024 Q2 or later
- NI-DCPower
- NI-SWITCH
- Recommended: InstrumentStudio 2024 Q2 or later (matching MeasurementLink)
- Recommended: TestStand 2021 SP1 or later

### Required Hardware

This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141)
and an NI-SWITCH (e.g. PXIe-2529).

By default, this example uses a physical instrument or a simulated instrument
created in NI MAX. To automatically simulate an instrument without using NI MAX,
follow the steps below:
- Create a `.env` file in the measurement service's directory or one of its
  parent directories (such as the root of your Git repository or
  `C:\ProgramData\National Instruments\MeasurementLink\Services` for statically
  registered measurement services).
- Add the following options to the `.env` file to enable simulation via the
  driver's option string:

  ```
  MEASUREMENTLINK_NIDCPOWER_SIMULATE=1 
  MEASUREMENTLINK_NIDCPOWER_BOARD_TYPE=PXIe
  MEASUREMENTLINK_NIDCPOWER_MODEL=4141
  MEASUREMENTLINK_NISWITCH_MULTIPLEXER_SIMULATE=1
  MEASUREMENTLINK_NISWITCH_MULTIPLEXER_TOPOLOGY=2529/2-Wire Dual 4x16 Matrix
  ```
