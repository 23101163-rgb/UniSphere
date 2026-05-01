from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    # Step 1: open root page
    driver.get(f"{BASE_URL}/")

    # Step 2: wait for page load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    current_url = driver.current_url.lower()
    page_text = driver.page_source.lower()

    print("Current URL:", driver.current_url)

    # Step 3: app root should redirect to login page
    assert "/accounts/login" in current_url, "Root page did not redirect to login page"

    # Step 4: login page content check
    assert (
        "login" in page_text or
        "welcome back" in page_text or
        "forgot your password" in page_text or
        "sign up" in page_text
    ), "Login page content not loaded properly"

    # Step 5: username/password fields exist
    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")

    assert username_field is not None, "Username field missing"
    assert password_field is not None, "Password field missing"

    print("Homepage Redirect Test Passed ✅")

finally:
    driver.quit()
