from setuptools import setup

# Version comes directly from source w/o importing
exec(open('closeio_api/_version.py').read())

requires = ['requests >= 2.11.1', 'grequests >= 0.3.0']

setup(
    name="closeio",
    packages=['closeio_api'],
    version=__version__,  # noqa
    description="Close.io Python Library",
    long_description="Closeio Python library",
    author="Close.io Team",
    url="https://github.com/closeio/closeio-api/",
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
    ]
)
