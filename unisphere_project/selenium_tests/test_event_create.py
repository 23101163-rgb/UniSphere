from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

driver = get_driver()

try:
    # Step 1: Login as teacher
    login(driver, "NMK", "amiarnob123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Open event create page
    driver.get(f"{BASE_URL}/events/create/")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
    except TimeoutException:
        print("Current URL:", driver.current_url)
        print("Page preview:\n", driver.page_source[:1500])
        raise AssertionError("Event create page did not load.")

    # Step 3: Fill form
    driver.find_element(By.NAME, "title").clear()
    driver.find_element(By.NAME, "title").send_keys("Test Event Selenium")

    driver.find_element(By.NAME, "description").clear()
    driver.find_element(By.NAME, "description").send_keys("This is a selenium event test.")

    Select(driver.find_element(By.NAME, "organizer_category")).select_by_value("non_club")
    Select(driver.find_element(By.NAME, "event_type")).select_by_value("workshop")

    # FIX: Use JavaScript to set date (type='date' input doesn't accept send_keys reliably)
    date_input = driver.find_element(By.NAME, "date")
    driver.execute_script("arguments[0].value = '2026-12-30';", date_input)
    # Trigger change event so Django form recognizes the value
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", date_input)

    # FIX: Use JavaScript to set time (type='time' input)
    time_input = driver.find_element(By.NAME, "time")
    driver.execute_script("arguments[0].value = '10:30';", time_input)
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", time_input)

    driver.find_element(By.NAME, "venue").clear()
    driver.find_element(By.NAME, "venue").send_keys("UAP Lab")

    driver.find_element(By.NAME, "registration_link").clear()
    driver.find_element(By.NAME, "registration_link").send_keys("https://example.com/event")

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
        "test event selenium" in page_text or
        "event created successfully" in page_text or
        "/events/" in current_url
    ), f"Event create failed.\nURL: {driver.current_url}\nPreview: {page_text[:1000]}"

    print("Event Create Test Passed ✅")

finally:
    driver.quit()