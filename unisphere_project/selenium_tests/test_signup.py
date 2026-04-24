from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = get_driver()

try:
    # Step 1: go to signup page
    driver.get(f"{BASE_URL}/accounts/register/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    # Step 2: fill form (unique username)
    username = f"user{int(time.time())}"

    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "first_name").send_keys("Test")
    driver.find_element(By.NAME, "last_name").send_keys("User")

    # 🔥 must be varsity email
    driver.find_element(By.NAME, "email").send_keys(f"{username}@uap-bd.edu")

    driver.find_element(By.NAME, "university_id").send_keys(f"UAP{int(time.time())}")

    driver.find_element(By.NAME, "password1").send_keys("12345678")
    driver.find_element(By.NAME, "password2").send_keys("12345678")

    # role select (if exists)
    try:
        driver.find_element(By.NAME, "role").send_keys("student")
    except:
        pass

    # Step 3: submit
    driver.find_element(By.TAG_NAME, "form").submit()

    # Step 4: wait for redirect (login/dashboard)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()

    assert (
        "login" in page_text or
        "dashboard" in page_text or
        "success" in page_text
    ), "Signup failed"

    print("Signup Test Passed ✅")

finally:
    driver.quit()