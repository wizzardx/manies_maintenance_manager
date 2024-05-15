# ruff: noqa

"""
Configuration file for the Sphinx documentation builder.

This file sets up the configuration for building the Sphinx documentation for
the "Marnie's Maintenance Manager" project. It includes path setup, project
information, and general configuration options.

- For a full list of configuration options, see:
  https://www.sphinx-doc.org/en/master/usage/configuration.html

Path Setup:
- Adds necessary directories to sys.path based on the environment (local or Read the
  Docs).
- Sets up Django environment variables and initializes Django settings.

Project Information:
- Project: "Marnie's Maintenance Manager"
- Author: David Purdy
- Copyright: 2024, David Purdy

General Configuration:
- Extensions: sphinx.ext.autodoc, sphinx.ext.napoleon
- Templates path: _templates (commented out)
- Exclude patterns: _build, Thumbs.db, .DS_Store

HTML Output Options:
- Theme: alabaster
- Custom static files path: _static (commented out)

Attributes:
    project (str): The name of the project.
    copyright (str): Copyright information.
    author (str): The name of the author.
    extensions (list): List of Sphinx extensions to be used.
    exclude_patterns (list): List of patterns to exclude from the documentation build.
    html_theme (str): The theme to use for HTML output.

Environment Variables:
    DATABASE_URL (str): URL for the database.
    DJANGO_SETTINGS_MODULE (str): Django settings module to use.
    DJANGO_READ_DOT_ENV_FILE (str): Flag to read .env file for Django.
    USE_DOCKER (str): Flag to determine if Docker is used.

Imports:
    os: Provides a portable way of using operating system-dependent functionality.
    sys: Provides access to some variables used or maintained by the Python interpreter.
    django: High-level Python web framework that encourages rapid development and
            clean, pragmatic design.

Example:
    To build the documentation, run:
        $ make html

"""

import os
import sys
import django

if os.getenv("READTHEDOCS", default="False") == "True":
    sys.path.insert(0, os.path.abspath(".."))
    os.environ["DJANGO_READ_DOT_ENV_FILE"] = "True"
    os.environ["USE_DOCKER"] = "no"
else:
    sys.path.insert(0, os.path.abspath("/app"))
os.environ["DATABASE_URL"] = "sqlite:///readthedocs.db"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

# -- Project information -----------------------------------------------------

# pylint: disable=invalid-name
project = "Marnie's Maintenance Manager"
copyright = """2024, David Purdy"""  # pylint: disable=redefined-builtin
author = "David Purdy"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]
