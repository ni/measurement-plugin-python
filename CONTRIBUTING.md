# Contributing to Measurement Plug-In SDK for Python

Contributions to Measurement Plug-In SDK for Python are welcome from all!

Measurement Plug-In SDK for Python is managed via [git](https://git-scm.com), with the canonical upstream
repository hosted on [GitHub](https://github.com/ni/measurement-plugin-python/). The repo contains templates and examples for developing measurement plug-ins in Python.

Measurement Plug-In SDK for Python follows a pull-request model for development.  If you wish to
contribute, you will need to create a GitHub account, fork this project, push a
branch with your changes to your project, and then submit a pull request.

Please remember to sign off your commits (e.g., by using `git commit -s` if you
are using the command-line client). This amends your git commit message with a line
of the form `Signed-off-by: Name LastName <name.lastmail@emailaddress.com>`. Please
include all authors of any given commit into the commit message with a
`Signed-off-by` line. This indicates that you have read and signed the Developer
Certificate of Origin (see below) and can legally submit your code to
this repository.

See [GitHub's official documentation](https://help.github.com/articles/using-pull-requests/) for more details.

# Getting Started

## Prerequisites

- (Optional) Install [Visual Studio Code](https://code.visualstudio.com/download).
- Install Git.
- Install Python and add it to the `PATH`. For the recommended Python version,
  see [Dependencies](README.md#dependencies).
- Install [Poetry](https://python-poetry.org/docs/#installation). Version >= 1.8.2

## Clone or Update the Git Repository

To download the Measurement Plug-In SDK for Python source, clone its Git
repository to your local PC.

```cmd
git clone --recurse-submodules https://github.com/ni/measurement-plugin-python.git
```

Specifying `--recurse-submodules` includes the
[ni-apis](https://github.com/ni/ni-apis) repository. This is required for the
[update gRPC stubs](#update-grpc-stubs-if-needed)
workflow.

If you already have the Git repository on your local PC, you can update it and
its submodules.

```cmd
git checkout main
git pull
git submodule update --init --recursive
```

## Select a Package to Develop

The Measurement Plug-In SDK for Python includes multiple Python packages:
- [ni_measurement_plugin_sdk_generator](/packages/generator/): Code generator
  for creating new Measurement Plug-In services and clients
- [ni_measurement_plugin_sdk_service](/packages/service/): Shared code used by
  Measurement Plug-In services and clients
- [ni_measurement_plugin_sdk](/packages/sdk/): Meta-package for installing both
  `ni_measurement_plugin_sdk_generator` and `ni_measurement_plugin_sdk_service`

Open a terminal window and `cd` to the package that you want to develop.

```cmd
cd packages\service
```

## Install the Package and Its Dependencies

From the package's subdirectory, run the [`poetry install`](https://python-poetry.org/docs/cli/#install) 
command. This creates an in-project virtual environment (`.venv`) and installs
the package's dependencies and dev-dependencies, as specified in its
`pyproject.toml` and `poetry.lock` files.

```cmd
poetry install
```

For `ni_measurement_plugin_sdk_service`, you may also want to install the
package's extra dependencies. This will install the NI driver API packages that
are supported for session management.

```cmd
poetry install --all-extras
```

## Activate the Virtual Environment (If Needed)

- (Preferred) Prefix commands with `poetry run`, e.g. `poetry run python measurement.py`
- In the command prompt: `poetry shell`
- In VS Code ([link](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment))

# Update gRPC Stubs (If Needed)

The `packages/service/ni_measurement_plugin_sdk_service/_internal/stubs` directory contains the
auto-generated Python files based on Measurement Plug-In protobuf (`.proto`) files. The file needs
to be replaced whenever there is a change to these `.proto` files:

- `ni/measurementlink/**/*.proto`
- `ni/grpcdevice/v1/session.proto`

The latest `.proto` files are available in the [ni-apis](https://github.com/ni/ni-apis) repo. This
repo includes the `ni-apis` repo as a Git submodule in `third_party/ni-apis`.

To regenerate the gRPC stubs, `cd` to the `packages/service` directory, install
it with `poetry install`, and run `poetry run python scripts/generate_grpc_stubs.py`. 
This generates the required `.py` files for the listed `.proto` files. The
required `grpcio-tools` package is already added as a development dependency in
`pyproject.toml`.

# Lint and Build Code

## Lint Code for Style and Formatting

Use [ni-python-styleguide](https://github.com/ni/python-styleguide) to lint the
code for style and formatting. This runs other tools such as `flake8`,
`pycodestyle`, and `black`.

```cmd
poetry run ni-python-styleguide lint
```

If there are any failures, try using `ni-python-styleguide` to fix them, then
lint the code again. If `ni-python-styleguide` doesn't fix the failures, you
will have to manually fix them.

```cmd
poetry run ni-python-styleguide fix
poetry run ni-python-styleguide lint
```

## Mypy Type Checking

Use [Mypy](https://pypi.org/project/mypy/) to type check the code.

```cmd
poetry run mypy
```

## Bandit Security Checks

Use [Bandit](https://pypi.org/project/bandit/) to check for common security issues.

```cmd
poetry run bandit -c pyproject.toml -r ni_measurement_plugin_sdk_service
```

For the exact command line for each package, see the corresponding Github workflows: [check_nimg.yml](/.github/workflows/check_nimg.yml) [check_nims.yml](/.github/workflows/check_nims.yml)

## Build Distribution Packages

To build distribution packages, run `poetry build`. This generates installable
distribution packages (source distributions and wheels) in the `dist`
subdirectory.

```cmd
poetry build
```

## Build Documentation

The `ni_measurement_plugin_sdk_service` package uses Sphinx to build API
reference documentation.

```cmd
poetry run sphinx-build _docs_source docs -b html -W --keep-going
```

The generated documentation is at `docs/index.html`.

# Testing

`ni-measurement-plugin-sdk-service` includes regression tests under the `tests/`
directory. The GitHub CI runs these tests for PRs targeting the main branch. It
is recommended that during development you run the tests locally before creating
a PR.

Some of the regression tests require InstrumentStudio and NI drivers to be
installed. 

In order to run the `ni-measurement-plugin-sdk-service` tests locally:

## Using Command Line

1. Install production dependencies and development dependencies into a venv by
running `poetry install --all-extras`.
2. Some tests will be skipped if the required components included with
InstrumentStudio are not installed. Install the latest version of
InstrumentStudio to run all tests.
3. Some tests require simulated hardware. Copy `examples\.env.simulation`
to the root measurement-plugin-python directory and rename it to `.env` to simulate
the required devices.

    ```ps
    cp .\examples\.env.simulation .env
    ```
4. Some DAQmx tests require persistent simulated devices created using `NI MAX` or
the `NI Hardware Configuration Utility`. They require a DAQmx device that supports
AI voltage measurements (e.g. PCIe-6363 or other X Series device). To simulate a
DAQmx device in software: open `NI MAX`, right-click `Devices and Interfaces`,
select `Create New...`, and select `Simulated NI-DAQmx Device or Modular
Instrument`. For the DAQmx tests to pass, you will need two DAQmx devices named 'Dev1'
and 'Dev2'.
5. Execute the command `poetry run pytest -v` to run the tests, from the repo's
   root directory.

    ``` ps
    (.venv) PS D:\git\measurement-plugin-python> poetry run pytest -v
    ```

## Using VS Code Test Explorer extension (UI)

Install and configure the `Python Test Explorer for Visual Studio Code`
extension to execute/debug the tests using UI. For more details related to the
extension, refer
[here](https://marketplace.visualstudio.com/items?itemName=LittleFoxTeam.vscode-python-test-adapter).

## Generate a Code Coverage Report

- Install the required dependency by running `poetry install`
- Run the command `poetry run pytest --cov=ni_measurement_plugin_sdk_service` to
  print a test coverage summary in the console window.
- Run the command `poetry run pytest --cov-report html:cov_html --cov=ni_measurement_plugin_sdk_service` 
  to generate detailed HTML based coverage report. Upon running, the coverage
  reports will be created under `<repo_root>\cov_html` directory.

# Adding Dependencies

You can add new dependencies using `poetry add` or by editing the `pyproject.toml` file.

When adding new dependencies, use a `>=` version constraint (instead of `^`)
unless the dependency uses semantic versioning.

# Developer Certificate of Origin (DCO)

   Developer's Certificate of Origin 1.1

   By making a contribution to this project, I certify that:

   (a) The contribution was created in whole or in part by me and I
       have the right to submit it under the open-source license
       indicated in the file; or

   (b) The contribution is based upon previous work that, to the best
       of my knowledge, is covered under an appropriate open source
       license and I have the right under that license to submit that
       work with modifications, whether created in whole or in part
       by me, under the same open-source license (unless I am
       permitted to submit under a different license), as indicated
       in the file; or

   (c) The contribution was provided directly to me by some other
       person who certified (a), (b) or (c) and I have not modified
       it.

   (d) I understand and agree that this project and the contribution
       are public and that a record of the contribution (including all
       personal information I submit with it, including my sign-off) is
       maintained indefinitely and may be redistributed consistent with
       this project or the open source license(s) involved.

(taken from [developercertificate.org](https://developercertificate.org/))

See [LICENSE](https://github.com/ni/measurement-plugin-python/blob/master/LICENSE)
for details about how Measurement Plug-In SDK for Python is licensed.
