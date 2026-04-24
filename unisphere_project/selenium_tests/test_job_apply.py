from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    login(driver, "Shifat", "amishifat123@#")

    # Step 1: go to jobs list page
    driver.get(f"{BASE_URL}/jobs/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "a"))
    )

    # Step 2: open first job detail dynamically
    opened = False
    for link in driver.find_elements(By.TAG_NAME, "a"):
        href = link.get_attribute("href")
        if href and "/jobs/" in href and href.rstrip('/').split('/')[-1].isdigit():
            link.click()
            opened = True
            break

    assert opened, "No job detail link found"

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 3: find Apply button/link dynamically
    apply_btn = None
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href")
        text = a.text.lower().strip()
        if (href and "/apply" in href) or ("apply now" in text):
            apply_btn = a
            break

    assert apply_btn is not None, "Apply button not found"

    apply_btn.click()

    # Step 4: wait for apply form
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "full_name"))
    )

    # Step 5: fill form
    full_name = driver.find_element(By.NAME, "full_name")
    full_name.clear()
    full_name.send_keys("Test User")

    email = driver.find_element(By.NAME, "email")
    email.clear()
    email.send_keys("test@test.com")

    phone = driver.find_element(By.NAME, "phone")
    phone.clear()
    phone.send_keys("01700000000")

    driver.find_element(By.NAME, "cover_letter").send_keys("I am interested in this job.")
    driver.find_element(By.NAME, "cv_link").send_keys("https://example.com/cv")

    # Step 6: submit
    driver.find_element(By.TAG_NAME, "form").submit()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()

    assert (
        "application was submitted successfully" in page_text or
        "applied" in page_text or
        "already applied" in page_text
    ), "Job apply failed"

    print("Job Apply Test Passed ✅")

finally:
    driver.quit()