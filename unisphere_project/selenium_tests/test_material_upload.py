from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

driver = webdriver.Chrome()
driver.get("http://127.0.0.1:8000/accounts/login/")


driver.find_element(By.NAME, "username").send_keys("Baivab")
driver.find_element(By.NAME, "password").send_keys("amibaivab123@#")
driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)

WebDriverWait(driver, 10).until(
    EC.url_contains("dashboard")
)


driver.get("http://127.0.0.1:8000/materials/create/")


print("Current URL:", driver.current_url)


try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
except:
    print("Page preview:\n", driver.page_source[:2000])
    raise AssertionError("Material create page did not load.")


driver.find_element(By.NAME, "title").send_keys("Test Material")
driver.find_element(By.NAME, "description").send_keys("Test Description")


file_path = os.path.abspath("test_files/test.pdf")
driver.find_element(By.NAME, "file").send_keys(file_path)


driver.find_element(By.TAG_NAME, "form").submit()

time.sleep(3)

assert "Test Material" in driver.page_source
print("✅ Material upload test passed")

driver.quit()

