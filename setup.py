from setuptools import setup

setup(
    name="closeio",
    packages=['closeio_api'],
    version="1.1",
    description="Close API Python Client",
    long_description="Close API Python Client",
    author="Close Team",
    url="https://github.com/closeio/closeio-api/",
    install_requires=[
        'requests >= 2.11.1'
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Operating System :: OS Independent",
    ]
)
