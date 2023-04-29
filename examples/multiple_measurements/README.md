## Multiple Measurements

This is a MeasurementLink example demonstrating how to interact with multiple measurement services
from TestStand.

### Features

- Uses the `nidcpower_source_dc_voltage` and `nidmm_measurement` example measurements
- Uses the `nidcpower` and `nidmm` packages to access NI-DCPower and NI-DMM from Python
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run multiple measurements
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-DCPower
- NI-DMM

### Required Measurement Services

Before running this example TestStand sequence, you must run or statically register the following
measurement services:

- [nidcpower_source_dc_voltage](../nidcpower_source_dc_voltage/)
- [nidmm_mesaurement](../nidmm_measurement/)

### Required Hardware

This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141) and an NI DMM
(e.g. PXI-4072).

To simulate an NI SMU or DMM in software: open `NI MAX`, right-click `Devices and Interfaces`,
select `Create New...`, and select `Simulated NI-DAQmx Device or Modular Instrument`.
SMUs are in the `Power Supplies` category. DMMs are in the `Digital Multimeters` category.