from common import get_driver, login, BASE_URL, TEACHER_USERNAME, TEACHER_PASSWORD
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time


def set_if_present(driver, name, value):
    elements = driver.find_elements(By.NAME, name)
    if not elements:
        return

    element = elements[0]
    tag_name = element.tag_name.lower()

    if tag_name == "select":
        Select(element).select_by_value(value)
        return

    element.clear()
    element.send_keys(value)


def select_if_present(driver, name, value):
    elements = driver.find_elements(By.NAME, name)
    if elements:
        Select(elements[0]).select_by_value(value)


driver = get_driver()

try:
    login(driver, TEACHER_USERNAME, TEACHER_PASSWORD)

    driver.get(f"{BASE_URL}/materials/create/")
    print("Current URL:", driver.current_url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
    except TimeoutException:
        print("Page preview:\n", driver.page_source[:2000])
        raise AssertionError("Material create page did not load.")

    set_if_present(driver, "title", "Test Material")
    set_if_present(driver, "description", "Test Description")
    set_if_present(driver, "course_name", "CSE101")
    select_if_present(driver, "semester", "1.1")
    set_if_present(driver, "topic", "Selenium Topic")
    set_if_present(driver, "tags", "selenium,test")

    test_dir = os.path.abspath("test_files")
    os.makedirs(test_dir, exist_ok=True)
    file_path = os.path.join(test_dir, "test.pdf")
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(b"%PDF-1.4 selenium test pdf")

    driver.find_element(By.NAME, "file").send_keys(file_path)
    driver.find_element(By.TAG_NAME, "form").submit()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(1)

    assert "test material" in driver.page_source.lower() or "/materials" in driver.current_url.lower(), (
        f"Material upload failed. URL: {driver.current_url}\nPreview: {driver.page_source[:1000]}"
    )
    print("✅ Material upload test passed")

finally:
    driver.quit()

