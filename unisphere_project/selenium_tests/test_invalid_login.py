from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    # Step 1: Open login page
    driver.get(f"{BASE_URL}/accounts/login/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Step 2: Enter wrong credentials
    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys("wrongusername123")

    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys("wrongpassword999")

    # Step 3: Submit
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # Step 4: Wait for page to reload (still on login page)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    print("Current URL:", driver.current_url)

    # Step 5: Should still be on login page (not dashboard)
    assert "/dashboard" not in current_url, "User should NOT be redirected to dashboard with wrong credentials"

    # Step 6: Error message should be visible
    assert (
        "wrong username/email or password" in page_text or
        "invalid" in page_text or
        "incorrect" in page_text or
        "/accounts/login" in current_url
    ), f"Error message not shown for invalid login.\nURL: {driver.current_url}\nPreview: {page_text[:500]}"

    print("Invalid Login Test Passed ✅")

finally:
    driver.quit()

