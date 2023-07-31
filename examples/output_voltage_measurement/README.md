## Output Voltage Measurement

This is a MeasurementLink example that sources DC voltage as input to the DUT with an NI SMU and measures the DUT output using NI-VISA DMM.

### Features

- Uses the `nidcpower` and `PyVISA` packages to access NI-DCPower and PyVISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Pin-aware, supporting one session and pin per instrument
  - Sources the DC voltage level on the selected pin/site
  - Measures output voltage in a single output pin/site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- For NI-DCPower, uses the NI gRPC Device Server to allow sharing the instrument sessions with other measurement services.

### Required Driver Software

- NI-DCPower
- NI-488.2 and/or NI-Serial
- NI-VISA
- Optional: NI Instrument Simulator software

Note: there is no Python instrument driver for the NI Instrument Simulator, so
this example directly performs low-level, device-specific commands and queries.

### Required Hardware

By default, this example does not require hardware; it uses a simulated instrument and PyVISA-sim to simulate NI-DCPower and NI-VISA DMM instruments in software. [`NIInstrumentSimulatorV2_0.yaml`](./NIInstrumentSimulatorV2_0.yaml) defines the behavior of the simulated NI-VISA DMM instrument.

This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141).

To use physical instruments, edit `measurement.py` to specify `USE_SIMULATION = False`

To use NI Instrument Simulator hardware:

- Connect the NI Instrument Simulator over GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your configuration, edit
    [`NIVisaDmmMeasurement.pinmap`](./NIVisaDmmMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.
