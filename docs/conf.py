"""Sphinx configuration."""
project = "Hypermodern-Starter"
author = "Maxim Podolski"
copyright = f"2020, {author}"
extensions = [
    "sphinx.ext.autodoc",  # Allows Sphinx to generate API doc from docstrings
    "sphinx.ext.napoleon",  # pre-processes Google-style docstrings to reStructuredText
    "sphinx_autodoc_typehints",  # Uses type annotations to document the types of function parameters
]
