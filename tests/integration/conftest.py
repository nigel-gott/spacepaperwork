import requests
import os
import time
import timeit

import pytest
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
    remote_server_url = 'http://firefox:4444/wd/hub'
    # wait_for_url(remote_server_url)

    return Browser(
        driver_name="remote",
        browser='firefox',
        command_executor=remote_server_url,
        desired_capabilities = {
        },
        keep_alive=True)


@pytest.fixture(scope="session")
def http_service():
    """Ensure that HTTP service is up and responsive."""
    url = "http://{}:{}/goosetools/".format("django",8000)
    wait_for_url(url)

    return url
    # `port_for` takes a container port and returns the corresponding host port


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except Exception:
        return False
