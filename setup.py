from setuptools import setup

requires = ['requests >= 0.10.8', 'grequests >= 0.2.0', 'six==1.9.0']

setup(
    name="closeio",
    packages=['closeio_api'],
    version="0.3",
    description="Close.io Python Library",
    long_description="Closeio Python library",
    author="Close.io Team",
    url="https://github.com/closeio/closeio-api/",
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Operating System :: OS Independent",
    ]
)
