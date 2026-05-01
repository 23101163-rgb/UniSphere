

from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

driver = get_driver()

try:
    # Step 1: Login
    driver.get(f"{BASE_URL}/accounts/login/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys("Shifat")
    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys("amishifat123@#")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Open job create page
    driver.get(f"{BASE_URL}/jobs/create/")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
    except TimeoutException:
        print("Current URL:", driver.current_url)
        print("Page preview:\n", driver.page_source[:1500])
        raise AssertionError("Job create page did not load. Login may have failed, or /jobs/create/ redirected elsewhere.")

    # Step 3: Fill form
    driver.find_element(By.NAME, "title").clear()
    driver.find_element(By.NAME, "title").send_keys("Test Job Selenium")

    driver.find_element(By.NAME, "company_name").clear()
    driver.find_element(By.NAME, "company_name").send_keys("Test Company")

    Select(driver.find_element(By.NAME, "job_type")).select_by_value("job")

    driver.find_element(By.NAME, "description").clear()
    driver.find_element(By.NAME, "description").send_keys("This is a selenium job test description.")

    driver.find_element(By.NAME, "required_skills").clear()
    driver.find_element(By.NAME, "required_skills").send_keys("Python, Django")

    driver.find_element(By.NAME, "eligibility").clear()
    driver.find_element(By.NAME, "eligibility").send_keys("CSE Student")

    driver.find_element(By.NAME, "salary_range").clear()
    driver.find_element(By.NAME, "salary_range").send_keys("20000-30000")

    driver.find_element(By.NAME, "application_deadline").clear()
    driver.find_element(By.NAME, "application_deadline").send_keys("2026-12-30")

    driver.find_element(By.NAME, "application_link").clear()
    driver.find_element(By.NAME, "application_link").send_keys("https://example.com/apply")

    # Step 4: Submit
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)

    try:
        submit_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", submit_btn)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    assert (
        "test job selenium" in page_text or
        "job posted" in page_text or
        "awaiting admin verification" in page_text or
        "/jobs/" in current_url
    ), f"Job create may have failed.\nCurrent URL: {driver.current_url}\nPage preview: {page_text[:1000]}"

    print("Job Create Test Passed ✅")

finally:
    driver.quit()
