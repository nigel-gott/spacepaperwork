import os
import time
import timeit

import pytest
import requests
from splinter.browser import Browser


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "local.yml")


def wait_until_responsive(check, timeout, pause, clock=timeit.default_timer):
    """Wait until a service is responsive."""

    ref = clock()
    now = ref
    while (now - ref) < timeout:
        if check():
            return
        time.sleep(pause)
        now = clock()

    raise WaitTimeoutException()


class WaitTimeoutException(Exception):
    pass


def wait_for_url(url):
    timeout_seconds = 60.0
    try:
        wait_until_responsive(
            timeout=timeout_seconds, pause=0.2, check=lambda: is_responsive(url)
        )
    except WaitTimeoutException:
        pytest.fail(f"Test timed out after {timeout_seconds}s waiting for {url}.")


@pytest.fixture(scope="session")
def browser():
    """Ensure that HTTP service is up and responsive."""
    remote_server_url = "http://firefox:4444/wd/hub"
    # wait_for_url(remote_server_url)

    return Browser(
        driver_name="remote",
        browser="firefox",
        command_executor=remote_server_url,
        desired_capabilities={},
        keep_alive=True,
    )


@pytest.fixture(scope="session")
def http_service():
    """Ensure that HTTP service is up and responsive."""
    url = "http://{}:{}/".format("django", 8000)
    wait_for_url(url)

    return url
    # `port_for` takes a container port and returns the corresponding host port


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except requests.ConnectionError:
        pass
    return False


# Skip integration tests unless --runslow flag is passed to pytest!
def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
