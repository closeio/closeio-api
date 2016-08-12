# NB: DO NOT RUN WITH IMPORTANT USERS API KEYS

The test suite destroys data from production before creating the fixtures data it needs, so be careful which api keys you use. You have been warned!

To run all tests:

`CLOSEIO_API_KEY=<your api key> python -m unittest discover tests`

To run a single test:

`CLOSEIO_API_KEY=<your api key> PYTHONPATH=. python tests/test_<path>.py`
