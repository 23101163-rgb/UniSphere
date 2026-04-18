from common import get_driver, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

driver = get_driver()

try:
    # Step 1: Login
    driver.get(f"{BASE_URL}/accounts/login/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys("ABaki")
    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys("amibaki123@#")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Find Logout
    logout_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
    )

    # Scroll to element
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", logout_link)

    # Try normal click, fallback to JS click
    try:
        logout_link.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", logout_link)

    # Step 3: Confirm login page এসেছে
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    page_text = driver.page_source.lower()
    current_url = driver.current_url.lower()

    assert (
        "login" in page_text or
        "sign in" in page_text or
        "/accounts/login" in current_url
    ), f"Logout may have failed.\nCurrent URL: {driver.current_url}\nPage text preview: {page_text[:500]}"

    print("Logout Test Passed ✅")

finally:
    driver.quit()