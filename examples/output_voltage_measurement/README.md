## Output Voltage Measurement

This is a MeasurementLink example that sources DC voltage as input to the DUT with an NI SMU and measures the DUT output with a DMM that supports SCPI commands using NI-VISA.

### Features

- Uses the `nidcpower` package to access NI-DCPower from Python
- Uses the open-source `PyVISA` package to access NI-VISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument resources with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Pin-aware, supporting one session and pin per instrument and a single site
  - Sources the DC voltage level of the DUT input pin
  - Measures the voltage of the DUT output pin
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- For NI-DCPower, uses the NI gRPC Device Server to allow sharing the instrument sessions with other measurement services.

### Required Driver Software

- NI-DCPower
- NI-488.2 and/or NI-Serial
- NI-VISA
- Optional: NI Instrument Simulator software

> **Note:**
>
> This example uses the custom instrument driver `_visa_dmm.py` to perform the device-specific commands and queries.

### Required Hardware

By default, this example does not require hardware; it uses a simulated instrument and PyVISA-sim to simulate NI-DCPower and NI-VISA DMM instruments in software. [`_visa_dmm_sim.yaml`](./_visa_dmm_sim.yaml) defines the behavior of the simulated NI-VISA DMM instrument.

Supported instrument models:
- NI Instrument Simulator v2.0
- HP/Agilent/Keysight 34401A DMM

By default, this example uses a physical instrument or a simulated device created in NI MAX. To automatically create a simulated device when running the measurement or TestStand sequence, follow the steps below:
- Create a `.env` file in the measurement service's directory or one of its parent directories (such as the root of your Git repository or `C:\ProgramData\National Instruments\MeasurementLink\Services` for statically registered measurement services).
- Add the following options to the `.env` file to enable simulation via the driver's option string:

  ```
  MEASUREMENTLINK_NIDCPOWER_SIMULATE=1 
  MEASUREMENTLINK_NIDCPOWER_BOARD_TYPE=PXIe
  MEASUREMENTLINK_NIDCPOWER_MODEL=4141

  MEASUREMENTLINK_VISA_DMM_SIMULATE=1
  ```

To use a physical instrument:
- This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141).
- Connect the instrument to a supported interface, such as GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your configuration, edit
    [`OutputVoltageMeasurement.pinmap`](./OutputVoltageMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.

To use a 3rd party DMM, such as a Keysight 34401A:
  - Verify the driver specific commands in `_visa_dmm.py` and update them if required.