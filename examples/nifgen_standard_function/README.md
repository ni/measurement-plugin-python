## NI-FGEN Standard Function

This is a MeasurementLink example that generates a standard function waveform
using an NI waveform generator.

### Features

- Uses the `nifgen` package to access NI-FGEN from Python
- Demonstrates how to cancel a running measurement by breaking a long wait into
  multiple short waits
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected sites
  - Outputs the same waveform configuration on all selected pin/site combinations
  - Does not synchronize waveforms
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence
- Uses the MeasurementLink session management service and NI gRPC Device Server

### Required Driver Software

- NI-FGEN

### Required Hardware

This example requires an NI waveform generator (e.g. PXIe-5423 (2CH)).