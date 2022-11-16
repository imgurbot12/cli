# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cli'
copyright = '2022, Andrew Scott'
author = 'Andrew Scott'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosectionlabel',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []

latex_documents = [(
    'index', 
    'cli3.tex', 
    'cli3 Documentation',
    'Andrew Scott', 
    'manual',
)]

man_pages=[(
    'index', 
    'cli3', 
    'cli3 Documentation',
    ['Andrew Scott', ], 
    1,
)]

texinfo_documents=[(
    'index', 
    'cli3', 
    'cli3 Documentation',
    'Andrew Scott', 
    'cli3', 
    'One line description of project.',
    'Miscellaneous',
)]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'default' # 'alabaster'
html_static_path = ['_static']
