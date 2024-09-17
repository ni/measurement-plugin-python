# Measurement Plug-In Generator for Python

- [Measurement Plug-In Generator for Python](#measurement-plug-in-generator-for-python)
  - [Introduction](#introduction)
  - [Dependencies](#dependencies)
  - [Developing Measurements: Quick Start](#developing-measurements-quick-start)
  - [Generating Measurement Clients: Quick Start](#generating-measurement-clients-quick-start)
    - [Installation](#installation)
    - [Generating a Minimal Python Measurement Client](#generating-a-minimal-python-measurement-client)
  - [Steps to Run/Debug the Measurement Client](#steps-to-rundebug-the-measurement-client)

---

## Introduction

`ni-measurement-plugin-sdk-generator` is a Python package containing tools for generating reusable measurement plug-ins and clients.

- `ni-measurement-plugin-generator` is a command for generating measurement plug-ins using gRPC services.
- `ni-measurement-plugin-client-generator` is a command for generating plug-in clients to interact with the measurement plug-ins.

For installation and usage, see [Measurement Plug-In SDK Service for Python (`ni-measurement-plugin-sdk-service`)](https://pypi.org/project/ni-measurement-plugin-sdk-service/).

---

## Dependencies

- Python >= 3.8 [(3.9 recommended)](https://www.python.org/downloads/release/python-3913/)
- [mako >= 1.2.1, < 2.x](https://pypi.org/project/Mako/1.2.1/)
- [click >= 8.1.3](https://pypi.org/project/click/8.1.3/)

---

## Developing Measurements: Quick Start

See the instructions [Measurement Plug-In SDK Service for Python (`ni-measurement-plugin-sdk-service`)](https://pypi.org/project/ni_measurement_plugin_sdk_service/#developing-measurements-quick-start) to develop a minimal measurement plug-in.

---

## Generating Measurement Clients: Quick Start

This section provides instructions to generate custom measurement clients in Python using Measurement Plug-In SDK for Python.

### Installation

Make sure the system has the recommended Python version is installed. Install Measurement Plug-In SDK for Python using [pip](https://pip.pypa.io/).

``` cmd
REM Activate the required virtual environment if any.
pip install ni-measurement-plugin-sdk-service
```

Check if you have installed the expected version of Measurement Plug-In SDK for Python installed by running the below command:

```cmd
pip show ni-measurement-plugin-sdk-service
```

### Generating a Minimal Python Measurement Client

1. Install the `ni-measurement-plugin-sdk-generator` package.

    ``` cmd
    REM Activate the required virtual environment if any.
    pip install ni-measurement-plugin-sdk-generator
    ```

2. Run the `ni-measurement-plugin-client-generator` tool. Use any of the command line arguments below to create Python measurement clients.

    1. Run this command with optional arguments to create measurement clients for specific measurements.

        ```ni-measurement-plugin-client-generator --measurement-service-class "ni.examples.SampleMeasurement_Python" --module-name "sample_measurement_client"  --class-name "SampleMeasurementClient" --directory-out <new_path_for_created_files>```

        - `--measurement-service-class` specifies the measurement service class for which the client is being generated.

        #### Optional:
        - `--module-name` and `--class-name` define the module and class names of the generated client. If not specified, they are derived from the measurement service class name.

        - `--directory-out` specifies the output directory for the generated files. If not specified, files are placed in the current directory.
        
        > **Note**: For multiple measurement client generation, `--module-name` and `--class-name` are ignored and derived from the service class of each measurement. So, ensure that the measurement service class name adheres to proper naming conventions.

    2. Run this command to create measurement clients for all registered measurements.

        `ni-measurement-plugin-client-generator --all`

        > **Note**: `--directory-out` can be provided for this command.

    3. Run this command to create measurement clients for any registered measurements interactively.

        `ni-measurement-plugin-client-generator --interactive`

3. The generated client includes four APIs: `measure`, `stream_measure`, `register_pin_map`, and `cancel`. The usage of these APIs is discussed in the section ["Steps to Run/Debug the Measurement Client".](#steps-to-rundebug-the-measurement-client)

> **Note**:
> - The Measurement Plug-In Client is compatible with all datatypes supported by the Measurement Plug-In.
> - The Double XY datatype is not supported for measurement configurations (inputs).
> - For Enum datatypes, the generated enum class names will be the measurement parameter name suffixed with 'Enum'. For instance, if the measurement parameter name is 'Enum In', the generated enum in the client will be `EnumInEnum'.
> - Ring control in LabVIEW measurements will be represented as numeric datatypes in the generated client.

### 

---

## Steps to Run/Debug the Measurement Client

1. Make sure the required measurement service is running before interacting with it via the client.

2. Use the client APIs from the ["Developing a Minimal Python MeasurementClient"](#developing-a-minimal-python-measurement-client) section.

    1. For non-streaming measurements, use `measure` method.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        outputs = client.measure()
        ```

    2. For streaming measurements, use `stream_measure` method.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        outputs_itr = client.stream_measure()
        for index, outputs in enumerate(outputs_itr):
            print(f"outputs[{index}] = {outputs}")
        ```

    3. If a measurement requires a pin map, it can be registered using the `register_pin_map` method. By default, `sites` is set to 0.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        client.register_pin_map(pin_map_path)
        output = client.measure()
        ```
        - Alternatively, you can provide a pin map context through the `pin_map_context` property. Similarly, sites can be provided through the `sites` property.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        client.pin_map_context = active_pin_map_context
        outputs = client.measure()
        ```

    4. Cancel any ongoing `measure` or `stream_measure` calls using the `cancel` method.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        thread = threading.Thread(target=client.measure)
        thread.start()
        client.cancel()
        ```

---
