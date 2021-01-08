from pathlib import Path

import pytest
import requests


def snapshot(browser, name):
    working_dir = Path().absolute()
    snapshot_path = working_dir / "misc_data" / f"{name}.html"
    browser.html_snapshot(str(snapshot_path.absolute()))


def wait_for(browser, element_id):
    if not browser.is_element_present_by_id(element_id, wait_time=10):
        snapshot(browser, f"cant_find_{element_id}")
        assert False


def wait_and_click(browser, element_id):
    wait_for(browser, element_id)
    button = browser.find_by_id(element_id).first
    button.click()


@pytest.mark.slow
def test_can_sign_up_and_create_new_fleet(http_service, browser):
    response = requests.get(http_service)
    assert response.status_code == 200

    browser.visit("http://django:8000/accounts/discord/login/")

    wait_for(browser, "id_previous_alliances")

    browser.fill("previous_alliances", "x")
    browser.fill("activity", "x")
    browser.fill("looking_for", "x")
    browser.fill("ingame_name", "x")

    wait_and_click(browser, "sign_up_button")

    browser.visit("http://django:8000/home")

    assert browser.is_text_present(
        "Your application is currently waiting confirmation by a member", wait_time=10
    )
