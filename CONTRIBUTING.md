# Contributing to Measurement Services Support for Python

Contributions to Measurement Services Support for Python are welcome from all!

Measurement Services Support for Python is managed via [git](https://git-scm.com), with the canonical upstream
repository hosted on [GitHub](https://github.com/ni/measurement-services-python/). The repo contains the necessary Python Measurement templates and examples to call into the Measurement Services.

Measurement Services Support for Python follows a pull-request model for development.  If you wish to
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

- Install the [Visual Studio Code](https://code.visualstudio.com/download).
- Install Git.
- Install [Poetry](https://python-poetry.org/docs/#installation).
- Install Python and add it to the PATH. (Recommended Version:3.8)

## Clone Repo

Clone the repo, this will pull the NI Measurement Service Framework components and related components.

```cmd
git clone https://github.com/ni/measurement-services-python.git
```

## Initializing the repo with .venv

From the root directory of the repo, initialize the project using the [poetry install](https://python-poetry.org/docs/cli/#install) command. This will set up a .venv with all the required dependencies based on poetry.lock file and pyproject.toml.

```cmd
poetry init 
```

## Ensure that the `./.venv` virtual environment is activated

- In the command prompt: `poetry shell`
- In the vscode ([link](https://code.visualstudio.com/docs/python/environments#_select-and-activate-an-environment))
- ALTERNATIVE: run commands with `poetry run`. i.e., `poetry run python measurement.py`

# Adding dependencies

Add dependency package for `ni_measurement_service`  using [poetry add](https://python-poetry.org/docs/cli/#add) command.

```cmd
poetry add <name_of_dependency>:<version>
```

Add **development dependencies** with the `-D` switch as shown below.

```cmd
poetry add -D <name_of_dev_dependency>:<version>
```

# Updating gRPC stubs when a .proto file is modified

The `ni_measurement_service\_internal\stubs` directory contains the auto-generated python files based on measurement services related protobuf (.proto) files. The file needs to be replaced whenever there is a change to these .proto files:

- DiscoveryServices.proto
- Measurement.proto
- ServiceLocation.proto
- ServiceManagement.proto

The latest .proto files are available in [Azure Repo](https://dev.azure.com/ni/DevCentral/_git/ASW?path=/Source/MeasurementServices/proto). From the Azure Repo manually download and overwrite the proto files under the `ni_measurement_service\_internal\stubs\proto` folder.

Run `poetry run python scripts/generate_grpc_stubs.py`. This generates the required *.py file for the listed proto files. The required `grpcio-tools` package is already added as a development dependency in pyproject.toml.

# Lint and Build Code

## Linting (correctly formatting) code

To check the code and update it for formatting errors

```cmd
poetry run ni-python-styleguide fix
```

## Building

```cmd
poetry build
```

Running this command from the repo's root directory will generate the tar.gz file and .whl file of ni_measurement_service package to the `dist` directory.

# Testing

`ni-measurement-service` includes tests under the directory `tests\` that exercises the python and grpc modules. The GitHub CI run these tests for PRs targeting the main branch. It is recommended that during development you run the tests locally before creating a PR.

In order to run the `ni-measurement-service` tests locally:

## Using Command Line

1. Install production dependencies and development dependencies into a venv by running `poetry install`.
2. Execute the command `poetry run pytest -v` to run the tests, from the repo's root directory.

    ``` ps
    (.venv) PS D:\TAF\measurement-services-python> poetry run pytest -v
    ```

## Using VS code Test Explorer extension(UI)

Install and configure the `Python Test Explorer for Visual Studio Code` extension to execute/debug the tests using UI. For more details related to the extension, refer [here](https://marketplace.visualstudio.com/items?itemName=LittleFoxTeam.vscode-python-test-adapter).

## Steps to generate code coverage report

- Install the required dependency by running `poetry install`
- Activate the virtual environment if not already activated : `.venv\Scripts\activate`
- Run the command `pytest --cov=ni_measurement_service`, from the repo's root directory **to get the summary of test coverage** in the console.
- Run the command `pytest --cov-report html:cov_html --cov=ni_measurement_service`, from the repo's root directory **to generate detailed HTML based coverage report**. Upon running, the coverage reports will be created under `<repo_root>\cov_html` directory.

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

See [LICENSE](https://github.com/ni/measurement-services-python/blob/master/LICENSE)
for details about how Measurement Services Support for Python is licensed.
