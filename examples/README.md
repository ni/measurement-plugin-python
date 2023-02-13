
# Examples

This directory contains the following example projects:  

- `sample_measurement`: Performs a loopback measurement with various data types. Provides a Measurement UI and a LabVIEW UI.
- `nidaqmx_analog_input`: Performs a finite analog input measurement with NI-DAQmx.
- `nidcpower_source_dc_voltage`: Sources and measures a DC voltage with an NI SMU. Provides a Measurement UI and a LabVIEW UI.
- `nidmm_measurement`: Performs a measurement using an NI DMM.
- `nifgen_standard_function`: Generates a standard function waveform using an NI waveform generator.
- `niscope_acquire_waveform`: Acquires a waveform using an NI oscilloscope.
- `niswitch_control_relays`: Controls relays using an NI relay driver (e.g. PXI-2567).
- `nivisa_dmm_measurement`: Performs a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0.

For more details about a specific example, see the `README.md` file included with the example.

### Setting up the Example Measurements

The example measurements shared are *poetry-based* projects. Follow the below steps to  for setting up the example measurement:

1. Install `poetry`. Refer to <https://python-poetry.org/docs/#installation> for information on installing poetry.

2. Open a command prompt, and change the working directory to the directory of the example measurement you want to work with.

    ``` cmd
    cd <path_of_example_measurement>
    REM Example: cd "..\measurementlink-python\examples\dc_measurement"
    ```

3. Run `poetry install`. This command creates/updates the .venv and installs all the dependencies(including `ni-measurementlink-service` package) needed for the Example into `.venv`

    ``` cmd
    poetry install
    ```
    - If you get a "command not found" error during `poetry install`, make sure that you added the Poetry path to the system path. Refer to [https://python-poetry.org/docs/#installing-with-the-official-installer/Add-poetry-to-your-path](https://python-poetry.org/docs/#installing-with-the-official-installer:~:text=Add%20Poetry%20to%20your%20PATH)
    ![PoetryInstallFail](../PoetryInstallFail.png)

> **Note**
> You can also run [`install_examples.py`](../scripts/install_examples.py) to set up all of the example measurements and install them into `C:\ProgramData\National Instruments\MeasurementLink\Services`.

### Executing the Example Measurements

1. Start the discovery service if not already started.
2. Use `poetry run` to run the measurement service:

    ``` cmd
    poetry run python measurement.py
    ```
