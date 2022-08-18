# Python Measurements

- [Python Measurements](#python-measurements)
  - [Introduction](#introduction)
  - [Abbreviations](#abbreviations)
  - [Dependencies](#dependencies)
  - [Examples](#examples)
    - [Setting Up an Example Measurement](#setting-up-an-example-measurement)
    - [Running an Example Measurement](#running-an-example-measurement)
  - [Developing Measurements: Quick Start](#developing-measurements-quick-start)
    - [Installation](#installation)
    - [Developing a Minimal Python Measurement](#developing-a-minimal-python-measurement)
  - [Manually Starting or Debugging a Measurement Service](#manually-starting-or-debugging-a-measurement-service)
  - [Static Registration of Python Measurements](#static-registration-of-python-measurements)
    - [Create a Batch File That Runs a Python Measurement](#create-a-batch-file-that-runs-a-python-measurement)
    - [Create Executable for Python Scripts](#create-executable-for-python-scripts)
  - [API References](#api-references)
  - [Appendix: Managing Measurement as Python Package (Project)](#appendix-managing-measurement-as-python-package-project)
    - [Create and Manage Python Measurement Package Using Poetry](#create-and-manage-python-measurement-package-using-poetry)
    - [Create and Manage Python Measurement Package Using `venv`](#create-and-manage-python-measurement-package-using-venv)
    - [Create and Manage Python Measurement Package by Directly Installing NIMS as a System-Level Package](#create-and-manage-python-measurement-package-by-directly-installing-nims-as-a-system-level-package)

---

## Introduction

`ni-measurement-service` (NIMS) is a Python framework that enables developers to quickly create Python measurements and run them as gRPC services.

---

## Dependencies

- Python >= 3.8 [(3.8 recommended)](https://www.python.org/downloads/release/python-3810/)
- [grpcio = 1.41.1](https://pypi.org/project/grpcio/1.41.1/)
- [protobuf = 3.19.1](https://pypi.org/project/protobuf/3.19.1/)
- [pywin32 >= 303 (Only for Windows)](https://pypi.org/project/pywin32/303/)

---

## Examples

The `examples` directory contains the following Python measurement example projects:

1. **Sample Measurement**: Demonstrates various configuration/output data types. Each configuration is copied to the corresponding output.
2. **DC Measurements**: Demonstrates how to use NI-DCPower to source a DC voltage and measure the resulting current and voltage.
    1. DC Measurement with Measurement UI
    2. DC Measurement with LabVIEW UI

### Setting Up an Example Measurement

1. Make sure the required Python version is installed.

2. Open a command prompt and change the working directory to the directory of the example measurement you want to work with.

    ``` cmd
    cd <path_of_example_measurement>
    REM Example: cd "..\measurement-services-python\examples\dc_measurement"
    ```

3. Create a Python virtual environment named `.venv`.

    ``` cmd
    python -m venv .venv
    ```

4. Install the example measurement's dependencies into `.venv`.

    ``` cmd
    .venv\Scripts\python -m pip install -r requirements.txt
    ```

Note: The example measurements do not "lock" or "pin" their dependencies, so this installs the latest versions available on PyPI. To install a local build of `ni-measurement-service`, specify `--find-links ../../dist` when running pip.

### Running an Example Measurement

1. Start the discovery service, if not already started.
   - (InstrumentStudio) Run InstrumentStudio and select `Manual layout`.

2. Manually start the example measurement service.

    ``` cmd
    .venv\Scripts\python measurement.py
    ```

3. Run the measurement.
   - InstrumentStudio
     - In the `Edit Layout` dialog, select the desired measurement and create a large panel.
     - In the measurement panel, specify the desired configuration and click `Run`.

For more details, see ["Manually Starting or Debugging a Measurement Service".](#manually-starting-or-debugging-a-measurement-service).

---

## Developing Measurements: Quick Start

This section provides instructions to develop custom Python measurement services using NIMS.

### Installation

Make sure the required Python version is installed. Install the NIMS Framework using [pip](https://pip.pypa.io/).

``` cmd
REM Activate the required virtual environment if any.
pip install ni-measurement-service
```

Check if you have installed the expected version of NIMS installed by running the below command:

```cmd
pip show ni-measurement-service
```

### Developing a Minimal Python Measurement

1. Open a command prompt and change the working directory to `ni_measurement_generator`.

    ``` cmd
    cd <path_of_template.py>
    REM Example: cd "..\measurement-services-python\ni_measurement_generator"
    ```

2. Run `template.py` in a command prompt using command line arguments for `display_name`, `version`, `measurement_type`, and `product_type`.
    1. Running `template` without optional arguments:

    `poetry run python ni-measurement-generator SampleMeasurement 0.1.0.0 Measurement Product`

    2. Running `template` with optional arguments for `ui_file`, `service_class`, `service_id`, and `description`:

    `poetry run python ni-measurement-generator SampleMeasurement 0.1.0.0 Measurement Product --ui-file MeasurementUI.measui --service-class SampleMeasurement_Python --service-id ECFC33EB-AA2E-41A5-A7C8-CAA2A8245052 --description description`

    3. Running `template` with optional argument `directory_out`:

    `poetry run python ni-measurement-generator SampleMeasurement 0.1.0.0 Measurement Product --directory-out <new_path_for_created_files>`


3. To customize the created measurement, provide metadata of the measurement's configuration (input parameters) and outputs (output parameters) in `measurement.py`.
    1. Use the `configuration()` decorator to provide metadata about the configurations. **The order of the configuration decorators must match the order of the function's positional parameters.**

        ``` python
        @foo_measurement_service.register_measurement
        #Display Names can not contains backslash or front slash.
        @foo_measurement_service.configuration("DisplayNameForInput1", DataType.String, "DefaultValueForInput1")
        @foo_measurement_service.configuration("DisplayNameForInput2", DataType.String, "DefaultValueForInput2")
        def measure(input_1, input_2):
            ''' A simple Measurement method'''
            return ["foo", "bar"]
        ```

    2. Use the `output()` decorator to provide metadata about the output. **The order of the output decorators must match the order of the list elements returned by the function.**

        ``` python
        @foo_measurement_service.register_measurement
        @foo_measurement_service.configuration("DisplayNameForInput1", nims.DataType.String, "DefaultValueForInput1")
        @foo_measurement_service.configuration("DisplayNameForInput2", nims.DataType.String, "DefaultValueForInput2")
        @foo_measurement_service.output("DisplayNameForOutput1", nims.DataType.String)
        @foo_measurement_service.output("DisplayNameForOutput2", nims.DataType.String)
        def measure(input_1, input_2):
            return ["foo", "bar"]
        ```

4. Run or debug the created measurement by following the steps discussed in the section ["Manually Starting or Debugging a Measurement Service".](#manually-starting-or-debugging-a-measurement-service)

---

## Manually Starting or Debugging a Measurement Service

1. Start the discovery service if not already started.

2. (Optional) Activate related virtual environments. Measurement developers can skip this step if they are not using any [virtual environments](#create-and-manage-python-measurement-package-using-venv) or [Poetry-based projects.](#create-and-manage-python-measurement-package-using-poetry)

    ```cmd
    .venv\scripts\activate
    ```

    - After successful activation, you can see the name of the environment, `(.venv)` is added to the command prompt.
    - If you face an access issue when trying to activate, retry after allowing scripts to run as Administrator by executing the below command in Windows PowerShell:

        ```cmd
        Set-ExecutionPolicy RemoteSigned
        ```

3. [Run](https://code.visualstudio.com/docs/python/python-tutorial#_run-hello-world)/[Debug](https://code.visualstudio.com/docs/python/debugging#_basic-debugging) the measurement python file created using NIMS.

4. To stop the running measurement service, press `Enter` in the terminal to properly close the service.

5. (Optional) After the usage of measurement, deactivate the virtual environment. Measurement developers can skip this step if they are not using any [virtual environments](#create-and-manage-python-measurement-package-using-venv) or [Poetry-based projects.](#create-and-manage-python-measurement-package-using-poetry)

    ```cmd
    deactivate
    ```

---

## Static Registration of Python Measurements

Refer to the [Static Registration of measurements section]() for the detailed steps needed to statically register a measurement.

To Statically register the examples provided, the user can copy the example directory with the service config file with the startup batch file, to the search paths and follow the [Setting Up the Example Measurements](#setting-up-the-example-measurements) section to set up the measurements.

Note: The startup batch file can be modified accordingly if the user wants to run with a custom Python distribution or virtual environment.

### Create a Batch File That Starts a Python Measurement Service

The batch file used for static registration is responsible for starting the Python measurement service.

Typical batch file:

``` cmd
"<path_to_python_exe>" "<path_to_measurement_file>"
```

Examples to start `measurement.py`:

1. Using the Python system distribution

    ```cmd
    python measurement.py
    ```

2. Using the virtual environment

    ```cmd
    REM Windows
    .venv\Scripts\python.exe measurement.py

    REM Linux
    .venv/bin/python measurement.py
    ```

### Create Executable for Python Scripts

To create an executable from a measurement, measurement authors can use the [PyInstaller](https://www.pyinstaller.org/) tooling. During the executable creation, the user can also embed the user interface file using the `--add-data "<path_of_the_UI_File>;."`.

Typical PyInstaller command to build executable:

```cmd
pyinstaller --onefile --console --add-data "<path_of_the_UI_File>;." --paths .venv\Lib\site-packages\ <path_of_the_measurement_script>
```

## API References

[Click here](https://ni.github.io/measurement-services-python/) to view the API reference documentation.

## Appendix: Managing Measurement as Python Package (Project)

A measurement and its related files can be maintained as a Python package. The basic components of any Python measurement package are:

1. Measurement service Python module (`.py`)
    - This file contains all the details related to the measurement and also contains the logic for the measurement execution.
    - This file is run to start the measurement as a service.

2. UI File
    - UI file for the Measurement. Types of supported UI files are:
        - Measurement UI (`.measui`): created using the **Measurement UI Editor application**.
        - LabVIEW UI (`.vi`)
    - The path and type of this file are configured by `ui_file_path` and `ui_file_type` respectively in `measurement_info` variable definition in the measurement service Python module.

Python communities have different ways of managing a Python package and its dependencies. It is up to the measurement developer, on how they wanted to maintain the package and dependencies. Measurement developers can choose from a few common approaches discussed below based on their requirements.

Note: Once we have the template support for Python measurement, the approach to managing the Python measurement package (project) will be streamlined and simplified.

### Create and Manage Python Measurement Package Using Poetry

1. Make sure the required Python version is installed.

2. Install Poetry using the installation steps given in <https://python-poetry.org/docs/#installation>.

3. Create a new Python project and add NIMS Framework as a dependency to the project.

    1. Open a command prompt, and change the working directory to the directory of your choice where you want to create the project.

        ``` cmd
        cd <path_of_directory_of_your_choice>
        ```

    2. Create a Python package (project) using the `poetry new` command. Poetry will create boilerplate files and folders that are commonly needed for a Python project.

        ``` cmd
        poetry new <name_of_the_project>
        ```

    3. Add the `ni-measurement-service` framework package as a dependency using the [poetry add command](https://python-poetry.org/docs/cli/#add).

        ``` cmd
        cd <name_of_the_project>
        poetry add ni-measurement-service
        ```

    4. The virtual environment will be auto-created by Poetry.

    5. Create measurement modules as described in ["Developing a Minimal Python Measurement"](#developing-a-minimal-python-measurement)
        - Any additional dependencies required by measurement can be added using [add command](https://python-poetry.org/docs/cli/#add).

            ``` cmd
            poetry add <dependency_package_name>
            ```

For detailed info on managing projects using Poetry [refer to the official documentation](https://python-poetry.org/docs/cli/).

### Create and Manage Python Measurement Package Using `venv`

1. Make sure the required Python version is installed.

2. Open a command prompt, and change the working directory to the directory of your choice where you want to create a project.

    ``` cmd
    cd <path_of_directory_of_your_choice>
    ```

3. Create a virtual environment.

    ``` cmd
    REM This creates a virtual environment named .venv
    python -m venv .venv
    ```

4. Activate the virtual environment. After successful activation

    ``` cmd
    .venv\scripts\activate
    REM Optionally upgrade the pip within the venv by executing the command
    python -m pip install -U pip
    ```

5. Install the `ni-measurement-service` package into the virtual environment.

    ``` cmd
    pip install ni-measurement-service
    ```

6. Create measurement modules as described in ["Developing a Minimal Python Measurement"](#developing-a-minimal-python-measurement)
    - Any additional dependencies required by measurement can be added pip install.

        ``` cmd
        pip install <dependency_package_name>
        ```

For detailed info on managing projects with a virtual environment [refer to the official documentation](https://docs.python.org/3/tutorial/venv.html).

### Create and Manage Python Measurement Package by Directly Installing NIMS as a System-Level Package

Measurement developers can also install the NIMS framework as a system package if their requirement is demanding.

1. Install the `ni-measurement-service` package from the command prompt

    ``` cmd
    pip install ni-measurement-service
    ```

2. Create measurement modules as described in ["Developing a Minimal Python Measurement"](#developing-a-minimal-python-measurement)

---
