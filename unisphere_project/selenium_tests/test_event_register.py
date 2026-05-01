from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    login(driver, "Shifat", "amishifat123@#")

    # Step 1: go to events page
    driver.get(f"{BASE_URL}/events/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "a"))
    )

    # Step 2: open first event
    links = driver.find_elements(By.TAG_NAME, "a")

    for link in links:
        href = link.get_attribute("href")
        if href and "/events/" in href and href.rstrip('/').split('/')[-1].isdigit():
            link.click()
            break

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # 🔥 Step 3: click register using URL (BEST METHOD)
    register_btn = None

    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href")
        if href and "/register" in href:
            register_btn = a
            break

    assert register_btn is not None, "Register button not found"

    register_btn.click()

    # Step 4: verify
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()

    assert (
        "cancel registration" in page_text or
        "registered" in page_text
    ), "Registration failed"

    print("Event Register Test Passed ✅")

finally:
    driver.quit()
