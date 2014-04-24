from setuptools import setup

requires = ['requests >= 0.10.8']

setup(
    name = "closeio",
    packages = ['closeio_api'],
    version = "0.1",
    description = "Close.io Python Library",
    author = "Close.io Team",
    url = "https://github.com/elasticsales/closeio-api/",
    install_requires = requires,
    classifiers = [
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        ],
    long_description = """\
        Closeio Python library
         """ )
