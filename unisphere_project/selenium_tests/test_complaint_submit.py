from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

driver = get_driver()

try:
    # Step 1: Login as student
    login(driver, "Adika", "amiadika123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Go to complaint submit page
    driver.get(f"{BASE_URL}/complaints/submit/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "subject"))
    )

    # Step 3: Fill form
    Select(driver.find_element(By.NAME, "target_type")).select_by_value("admin")
    Select(driver.find_element(By.NAME, "category")).select_by_value("infrastructure")

    driver.find_element(By.NAME, "subject").clear()
    driver.find_element(By.NAME, "subject").send_keys("Selenium Complaint Test")

    driver.find_element(By.NAME, "description").clear()
    driver.find_element(By.NAME, "description").send_keys("This is a test complaint submitted by Selenium.")

    # Check anonymous box
    anon_checkbox = driver.find_element(By.NAME, "is_anonymous")
    if not anon_checkbox.is_selected():
        driver.execute_script("arguments[0].click();", anon_checkbox)

    # Step 4: Submit
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)

    try:
        submit_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", submit_btn)

    # Step 5: Verify
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    assert (
        "selenium complaint test" in page_text or
        "complaint submitted" in page_text or
        "/complaints/my" in current_url
    ), f"Complaint submit failed.\nURL: {driver.current_url}\nPreview: {page_text[:1000]}"

    print("Complaint Submit Test Passed ✅")

finally:
    driver.quit()

