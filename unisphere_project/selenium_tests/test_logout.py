from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

driver = webdriver.Chrome()

try:
    wait = WebDriverWait(driver, 10)

    driver.get("http://127.0.0.1:8000/accounts/login/")
    driver.maximize_window()

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("teacher1")
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys("StrongPass123")
    password_input.send_keys(Keys.RETURN)

    wait.until(EC.url_contains("/accounts/dashboard"))

    logout_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Logout")))
    logout_link.click()

    wait.until(EC.url_contains("/accounts/login"))

    print("After logout URL:", driver.current_url)
    assert "/accounts/login" in driver.current_url.lower()

    driver.get("http://127.0.0.1:8000/accounts/dashboard/")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Protected page redirect URL:", driver.current_url)
    assert "/accounts/login" in driver.current_url.lower()

    print("Logout test passed!")

except Exception as e:
    print("Logout test failed!")
    print("Error type:", type(e).__name__)
    print("Error:", e)
    traceback.print_exc()
    driver.save_screenshot("logout_failure.png")
    print("Screenshot saved as logout_failure.png")

finally:
    driver.quit()