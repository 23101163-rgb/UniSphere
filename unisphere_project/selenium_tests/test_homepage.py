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

    page_text = driver.find_element(By.TAG_NAME, "body").text
    print("Current URL:", driver.current_url)
    print("Page text:\n", page_text)

    assert "dashboard" in driver.current_url.lower()
    assert "welcome" in page_text.lower()
    assert "study materials" in page_text.lower()

    print("Homepage test passed!")

except Exception as e:
    print("Homepage test failed!")
    print("Error type:", type(e).__name__)
    print("Error:", e)
    traceback.print_exc()
    driver.save_screenshot("homepage_failure.png")
    print("Screenshot saved as homepage_failure.png")

finally:
    driver.quit()