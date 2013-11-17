from setuptools import setup
import sys

requires = ['requests>=0.10.8']

setup(
    name = "closeio_api",
    py_modules = ['closeio_api'],
    version = "0.1",
    description = "Closeio Python library",
    author = "Closeio Team",
    url = "https://github.com/elasticsales/closeio-api/",
    install_requires = requires,
    classifiers = [
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        ],
    long_description = """\
        Closeio Python library
         """ )
