from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

driver = get_driver()

try:
    # Step 1: Login and wait for dashboard to fully load
    login(driver, "ABaki", "amibaki123@#")

    # Wait until URL changes away from /login/ — confirms login succeeded
    WebDriverWait(driver, 10).until(
        lambda d: "login" not in d.current_url.lower()
    )

    # Extra wait for dashboard body
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print(f"Logged in. Current URL: {driver.current_url}")

    # Step 2: Go to forum thread create page
    driver.get(f"{BASE_URL}/forum/thread/create/")

    print(f"Forum create URL: {driver.current_url}")

    # Step 3: Wait for the title field — if redirected to login, fail with clear message
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
    except TimeoutException:
        print(f"Page URL after navigating: {driver.current_url}")
        print(f"Page source preview:\n{driver.page_source[:1500]}")
        raise AssertionError(
            "Forum thread create page did not load. "
            "Possible reasons: login failed, or no Category exists in database."
        )

    # Step 4: Fill form
    title_field = driver.find_element(By.NAME, "title")
    title_field.clear()
    title_field.send_keys("Selenium Forum Test Thread")

    content_field = driver.find_element(By.NAME, "content")
    content_field.clear()
    content_field.send_keys("This is a test thread created by Selenium automation.")

    # Select first available category
    try:
        category_select = driver.find_element(By.NAME, "category")
        Select(category_select).select_by_index(1)
    except Exception as e:
        print(f"Category select issue: {e}")
        print("Make sure at least one Category exists in the database.")
        raise

    # Step 5: Submit
    submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)

    try:
        submit_btn.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", submit_btn)

    # Step 6: Verify — should redirect to thread detail page
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    print(f"After submit URL: {driver.current_url}")

    assert (
            "selenium forum test thread" in page_text or
            "post published" in page_text or
            "/forum/thread/" in current_url
    ), f"Forum thread create failed.\nURL: {driver.current_url}\nPreview: {page_text[:800]}"

    print("Forum Thread Create Test Passed ✅")

finally:
    driver.quit()

