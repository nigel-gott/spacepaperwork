import requests


def test_read_and_write(http_service):
    response = requests.get(http_service)

    assert response.status_code == 200
