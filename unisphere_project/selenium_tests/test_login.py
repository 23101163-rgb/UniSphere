from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

driver = webdriver.Chrome()

try:
    driver.get("http://127.0.0.1:8000/accounts/login/")
    driver.maximize_window()

    wait = WebDriverWait(driver, 10)

    username_input = wait.until(
        EC.presence_of_element_located((By.NAME, "username"))
    )
    password_input = driver.find_element(By.NAME, "password")

    username_input.send_keys("teacher1")
    password_input.send_keys("StrongPass123")
    password_input.send_keys(Keys.RETURN)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Current URL:", driver.current_url)
    print("Page title:", driver.title)
    print("Page text:\n", driver.find_element(By.TAG_NAME, "body").text)

    assert "dashboard" in driver.current_url.lower()
    print("Login test passed!")

except Exception as e:
    print("Login test failed!")
    print("Error type:", type(e).__name__)
    print("Error:", e)
    traceback.print_exc()
    driver.save_screenshot("login_failure.png")
    print("Screenshot saved as login_failure.png")

finally:
    driver.quit()