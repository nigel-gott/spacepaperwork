import requests
import os
import time
import timeit

import pytest
from requests.exceptions import ConnectionError
from pytest_docker.plugin import Services


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "local.yml")


def wait_until_responsive(self, check, timeout, pause, clock=timeit.default_timer):
    """Wait until a service is responsive."""

    ref = clock()
    now = ref
    while (now - ref) < timeout:
        if check():
            return
        time.sleep(pause)
        now = clock()

    # get container logs to provide info about failure
    output = self._docker_compose.execute("logs").decode("utf-8")

    raise WaitTimeoutException(container_logs=output)


Services.wait_until_responsive = wait_until_responsive


class WaitTimeoutException(Exception):
    def __init__(
        self, container_logs, message="Timeout reached while waiting on service!"
    ):
        self.container_logs = container_logs
        super().__init__(message)


@pytest.fixture(scope="session")
def http_service(docker_ip, docker_services):
    """Ensure that HTTP service is up and responsive."""

    # `port_for` takes a container port and returns the corresponding host port
    port = docker_services.port_for("django", 8000)
    url = "http://{}:{}/goosetools/".format(docker_ip, port)
    timeout_seconds = 60.0
    try:
        docker_services.wait_until_responsive(
            timeout=timeout_seconds, pause=0.2, check=lambda: is_responsive(url)
        )
    except WaitTimeoutException as ex:
        pytest.fail(
            f"Test timed out after {timeout_seconds}s waiting for {url}. The container logs were {ex.container_logs}"
        )
    return url


def is_responsive(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
    except ConnectionError:
        return False
