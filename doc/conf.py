"""Sphinx configuration for the pyidfm documentation."""

import os
import sys
from datetime import datetime

# Make the pyidfm package importable for autodoc.
sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "PyIDFM"
author = "Robin David"
copyright = f"{datetime.now().year}, {author}"

# Pulled from pyproject.toml at build time would be cleaner, but a plain string
# keeps the doc build dependency-free.
release = "0.1.0"
version = release


# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# MyST extensions to allow the documentation to feel modern (admonitions,
# fenced code, anchors, etc.).
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "smartquotes",
    "substitution",
    "tasklist",
]
myst_heading_anchors = 3

# Autodoc behavior.
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autoclass_content = "both"
autosummary_generate = True

# Napoleon supports both Google- and Sphinx-style docstrings; pyidfm uses the
# Sphinx `:param:` style.
napoleon_google_docstring = False
napoleon_numpy_docstring = False

# Cross-references to the Python stdlib and requests.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
}


# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_book_theme"
html_title = "PyIDFM"
html_static_path = ["_static"]

html_theme_options = {
    "repository_url": "https://github.com/RobinDavid/pyidfm",
    "repository_branch": "main",
    "path_to_docs": "doc",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "use_download_button": False,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
    "navigation_with_keys": True,
}

# Copy-button: strip the prompt characters so users can copy snippets cleanly.
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
