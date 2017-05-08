from setuptools import setup

setup(
    name="closeio",
    packages=['closeio_api'],
    version="1.0",
    description="Close.io Python Library",
    long_description="Closeio Python library",
    author="Close.io Team",
    url="https://github.com/closeio/closeio-api/",
    install_requires=[
        'requests >= 2.11.1'
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
    ]
)
