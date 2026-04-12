from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import traceback

driver = webdriver.Chrome()

try:
    wait = WebDriverWait(driver, 10)

    driver.get("http://127.0.0.1:8000/accounts/login/")
    driver.maximize_window()

    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys("teacher1")
    password = driver.find_element(By.NAME, "password")
    password.send_keys("StrongPass123")
    password.send_keys(Keys.RETURN)

    wait.until(EC.url_contains("/accounts/dashboard"))

    driver.get("http://127.0.0.1:8000/materials/create/")
    wait.until(EC.presence_of_element_located((By.NAME, "title")))

    driver.find_element(By.NAME, "title").send_keys("Selenium Uploaded Material")
    driver.find_element(By.NAME, "description").send_keys("Uploaded by selenium")
    driver.find_element(By.NAME, "course_name").send_keys("CSE201")

    semester_field = driver.find_element(By.NAME, "semester")
    semester_field.send_keys("Year 1 Semester 1")

    driver.find_element(By.NAME, "topic").send_keys("Testing")
    driver.find_element(By.NAME, "tags").send_keys("selenium,test")

    file_path =r"C:\Users\User\Downloads\CSE315_MidExam_Notes.pdf"
    driver.find_element(By.NAME, "file").send_keys(file_path)

    driver.find_element(By.TAG_NAME, "form").submit()

    time.sleep(2)

    page_text = driver.find_element(By.TAG_NAME, "body").text
    print("Current URL:", driver.current_url)
    print("Page text:\n", page_text)

    assert "uploaded successfully" in page_text.lower()
    print("Material upload test passed!")

except Exception as e:
    print("Material upload test failed!")
    print("Error type:", type(e)._name_)
    print("Error:", e)
    traceback.print_exc()
    driver.save_screenshot("material_upload_failure.png")
    print("Screenshot saved as material_upload_failure.png")

finally:
    driver.quit()