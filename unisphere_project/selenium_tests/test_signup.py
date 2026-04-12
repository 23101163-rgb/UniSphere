from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback

driver = webdriver.Chrome()

try:
    wait = WebDriverWait(driver, 10)

    unique_suffix = str(int(time.time()))
    username = f"seleniumuser{unique_suffix}"
    email = f"selenium{unique_suffix}@uap-bd.edu"
    university_id = f"88{unique_suffix[-6:]}"
    password_value = "StrongPass123"

    driver.get("http://127.0.0.1:8000/accounts/register/")
    driver.maximize_window()

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "university_id").send_keys(university_id)
    driver.find_element(By.NAME, "first_name").send_keys("Selenium")
    driver.find_element(By.NAME, "last_name").send_keys("User")

    role_select = Select(driver.find_element(By.NAME, "role"))
    role_select.select_by_value("student")

    driver.find_element(By.NAME, "password1").send_keys(password_value)
    driver.find_element(By.NAME, "password2").send_keys(password_value)

    driver.find_element(By.TAG_NAME, "form").submit()

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Current URL:", driver.current_url)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    print("Page text:\n", page_text)

    assert "dashboard" in driver.current_url.lower()
    print("Signup test passed!")

except Exception as e:
    print("Signup test failed!")
    print("Error type:", type(e).__name__)
    print("Error:", e)
    traceback.print_exc()
    driver.save_screenshot("signup_failure.png")
    print("Screenshot saved as signup_failure.png")

finally:
    driver.quit()S