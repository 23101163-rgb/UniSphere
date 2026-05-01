from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    # Open login page
    driver.get(f"{BASE_URL}/accounts/login/")

    # Wait for login form to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Enter credentials
    driver.find_element(By.NAME, "username").send_keys("ARaiyan")
    driver.find_element(By.NAME, "password").send_keys("amiraiyan123@#")

    # Click login button
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Wait for redirect to dashboard
    WebDriverWait(driver, 10).until(
        EC.url_contains("dashboard")
    )

    # Debug info (optional but helpful)
    print("Current URL:", driver.current_url)

    # Assertion (reliable)
    assert "/dashboard" in driver.current_url, "Login failed - not redirected to dashboard"

    print("Login Test Passed ✅")

finally:
    driver.quit()
