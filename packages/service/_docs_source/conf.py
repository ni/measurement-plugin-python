"""Sphinx Configuration File."""

import datetime
import pathlib

import autoapi.extension
import toml

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "autoapi.extension",
    "m2r2",
    "sphinx_click",
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

root_path = pathlib.Path(__file__).parent.parent
pyproj_file = root_path / "pyproject.toml"
proj_config = toml.loads(pyproj_file.read_text())


project = proj_config["tool"]["poetry"]["name"]
company = "National Instruments"
year = str(datetime.datetime.now().year)
copyright = f"{year}, {company}"


# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
version = proj_config["tool"]["poetry"]["version"]
release = ".".join(version.split(".")[:2])
description = proj_config["tool"]["poetry"]["description"]


htmlhelp_basename = f"{project}doc"


# tell autoapi to doc the public options
autoapi_options = list(autoapi.extension._DEFAULT_OPTIONS)
autoapi_options.remove("private-members")  # note: remove this to include "_" members in docs
autoapi_dirs = [root_path / "ni_measurement_plugin_sdk_service"]
autoapi_type = "python"
autodoc_typehints = "description"


# WARNING: more than one target found for cross-reference 'MeasurementInfo':
# ni_measurement_plugin_sdk_service.MeasurementInfo,
# ni_measurement_plugin_sdk_service.measurement.info.MeasurementInfo
#
# TODO: figure out how to make :canonical: work with autoapi
def skip_aliases(app, what, name, obj, skip, options):
    """Skip documentation for classes that are exported from multiple modules."""
    # For names that are defined in a public sub-module and aliased into a
    # public package, hide the alias.
    if name in [
        "ni_measurement_plugin_sdk_service.DataType",
        "ni_measurement_plugin_sdk_service.MeasurementInfo",
        "ni_measurement_plugin_sdk_service.ServiceInfo",
        "ni_measurement_plugin_sdk_service.MeasurementService",
    ]:
        skip = True

    # For names that are defined in a private sub-module and aliased into a
    # public package, hide the definition.
    if name.startswith("ni_measurement_plugin_sdk_service.session_management._constants."):
        skip = True

    return skip


def setup(sphinx):
    """Sphinx setup callback."""
    sphinx.connect("autoapi-skip-member", skip_aliases)


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


intersphinx_mapping = {
    "nidaqmx": ("https://nidaqmx-python.readthedocs.io/en/stable/", None),
    "nidcpower": ("https://nidcpower.readthedocs.io/en/stable/", None),
    "nidigital": ("https://nidigital.readthedocs.io/en/stable/", None),
    "nidmm": ("https://nidmm.readthedocs.io/en/stable/", None),
    "nifgen": ("https://nifgen.readthedocs.io/en/stable/", None),
    "niscope": ("https://niscope.readthedocs.io/en/stable/", None),
    "niswitch": ("https://niswitch.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3", None),
}


# -- Options for HTML output ----------------------------------------------


# The theme to use for HTML and HTML Help pages. See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": -1,
}

# Napoleon settings
napoleon_numpy_docstring = False
