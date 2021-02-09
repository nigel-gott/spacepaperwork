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
def test_can_sign_up(http_service, browser):
    response = requests.get(http_service)
    assert response.status_code == 200

    # The default uid already has a user account setup from the users/fixture/dev.json fixture, switch to an unknown discord user to test signup.
    browser.visit("http://django:8000/stub_discord_auth/set_uid/100001234")
    browser.visit("http://django:8000/accounts/discord/login/")

    wait_and_click(browser, "conduct_button")
    wait_and_click(browser, "agree_button")

    wait_for(browser, "id_ingame_name")

    browser.fill("ingame_name", "x")

    wait_and_click(browser, "sign_up_button")

    browser.visit("http://django:8000/home")

    assert browser.is_text_present(
        "Your application is currently waiting confirmation by a member", wait_time=10
    )
