## NI-VISA DMM Measurement

This is a measurement plug-in example that performs a DMM measurement using NI-VISA
and a DMM that supports SCPI commands.

### Features

- Uses the open-source `PyVISA` package to access NI-VISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Pin-aware, supporting a custom instrument type and a single session/pin/site
- Includes InstrumentStudio and Measurement Plug-In UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument resources with the session management service, and run a
  measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and
    session registration and unregistration in the `Setup` and `Cleanup`
    sections of the main sequence. For **Test UUTs** and batch process model use
    cases, these steps should be moved to the `ProcessSetup` and
    `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Software

- InstrumentStudio 2025 Q1 or later
- NI-488.2 and/or NI-Serial
- NI-VISA
- Recommended: TestStand 2021 SP1 or later
- Optional: NI Instrument Simulator software

> **Note:**
>
> This example uses the custom instrument driver `_visa_dmm.py` to perform the
> device-specific commands and queries.

### Required Hardware

Supported instrument models:
- NI Instrument Simulator v2.0
- HP/Agilent/Keysight 34401A DMM

By default, this example uses a physical instrument. To simulate an instrument
in software, follow the steps below:
- Create a `.env` file in the measurement service's directory or one of its
  parent directories (such as the root of your Git repository or
  `C:\ProgramData\National Instruments\Plug-Ins\Measurements` for statically
  registered measurement services).
- Add the following option to the `.env` file to enable simulation via the
  driver's `simulate` parameter:

  ```
  MEASUREMENT_PLUGIN_VISA_DMM_SIMULATE=1
  ```

The `_visa_dmm.py` instrument driver implements simulation using PyVISA-sim.
[`_visa_dmm_sim.yaml`](./_visa_dmm_sim.yaml) defines the behavior of the
simulated instrument.

To use a physical instrument:
- Connect the instrument to a supported interface, such as GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your instrument's configuration, edit
    [`NIVisaDmmMeasurement.pinmap`](./NIVisaDmmMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.
  - To configure third party instruments, see the documentation provided with
    the instrument.
