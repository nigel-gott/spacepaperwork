from pathlib import Path
import requests
from splinter import Browser
browser = Browser('firefox', headless=True)

def snapshot(name):
    working_dir = Path().absolute()
    snapshot_path = working_dir / "misc_data" /  f"{name}.html"
    browser.html_snapshot(str(snapshot_path.absolute()))

  
def wait_and_click(element_id):
    if not browser.is_element_present_by_id(element_id, wait_time=10):
        snapshot(f'cant_find_{element_id}')
        assert False
    button = browser.find_by_id(element_id).first
    print(button.outer_html)
    button.click()



def test_can_sign_up_and_create_new_fleet(http_service):
    response = requests.get(http_service)
    assert response.status_code == 200

    browser.visit('http://localhost:8000/goosetools')

    wait_and_click('sign_up_button')

    wait_and_click('start_new_fleet_button')
    browser.find_by_id('id_name').first.fill("Test Fleet Name")
    wait_and_click('create_fleet_button')

    assert browser.is_text_present("Active Fleets", wait_time=10)
    assert browser.is_text_present("Test Fleet Name", wait_time=10)
  
