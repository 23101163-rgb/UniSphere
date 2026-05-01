from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = get_driver()

try:
    # Step 1: Go to signup page
    driver.get(f"{BASE_URL}/accounts/register/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Step 2: Fill form with NON-UAP email (gmail.com)
    username = f"baduser{int(time.time())}"

    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "first_name").send_keys("Bad")
    driver.find_element(By.NAME, "last_name").send_keys("Email")

    # 🔥 Invalid domain — should be rejected
    driver.find_element(By.NAME, "email").send_keys(f"{username}@gmail.com")

    driver.find_element(By.NAME, "university_id").send_keys(f"BAD{int(time.time())}")

    driver.find_element(By.NAME, "password1").send_keys("StrongPass123")
    driver.find_element(By.NAME, "password2").send_keys("StrongPass123")

    try:
        driver.find_element(By.NAME, "role").send_keys("student")
    except:
        pass

    # Step 3: Submit
    driver.find_element(By.TAG_NAME, "form").submit()

    # Step 4: Wait
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    print("Current URL:", driver.current_url)

    # Step 5: Should NOT be redirected to dashboard
    assert "/dashboard" not in current_url, "User with invalid email should NOT reach dashboard"

    # Step 6: Error message should appear
    assert (
        "university email" in page_text or
        "uap-bd.edu" in page_text or
        "invalid" in page_text or
        "/register" in current_url
    ), f"No validation error for invalid email domain.\nURL: {driver.current_url}\nPreview: {page_text[:500]}"

    print("Signup Validation Test Passed ✅")

finally:
    driver.quit()

