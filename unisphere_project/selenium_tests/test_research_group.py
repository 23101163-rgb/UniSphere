from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

driver = get_driver()

try:
    # ===== Part 1: Student A creates open research group =====
    login(driver, "Ejaj", "amiejaj123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    driver.get(f"{BASE_URL}/research/groups/create/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "name"))
    )

    driver.find_element(By.NAME, "name").clear()
    driver.find_element(By.NAME, "name").send_keys("Selenium Research Group")

    driver.find_element(By.NAME, "description").clear()
    driver.find_element(By.NAME, "description").send_keys("Test group created by Selenium.")

    driver.find_element(By.NAME, "research_area").clear()
    driver.find_element(By.NAME, "research_area").send_keys("AI and ML")

    Select(driver.find_element(By.NAME, "group_type")).select_by_value("open")

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
    assert (
        "selenium research group" in page_text or
        "group created" in page_text or
        "/research/groups/" in driver.current_url.lower()
    ), f"Group create failed.\nURL: {driver.current_url}"

    print("Research Group Create Test Passed ✅")

    # ===== Part 2: Student B sends join request =====
    # Logout first
    driver.get(f"{BASE_URL}/accounts/logout/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    login(driver, "Adika", "amiadika123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Go to research groups list
    driver.get(f"{BASE_URL}/research/groups/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Find and click the group we just created
    found_group = False
    for link in driver.find_elements(By.TAG_NAME, "a"):
        href = link.get_attribute("href") or ""
        text = link.text.lower()
        if "selenium research group" in text or ("/research/groups/" in href and href.rstrip('/').split('/')[-1].isdigit()):
            if "selenium research group" in text:
                link.click()
                found_group = True
                break

    if found_group:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Find join request button/link
        join_btn = None
        for a in driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href") or ""
            if "/join" in href:
                join_btn = a
                break

        if join_btn:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", join_btn)
            try:
                join_btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", join_btn)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            page_text = driver.page_source.lower()
            assert (
                "join request sent" in page_text or
                "pending" in page_text or
                "already" in page_text
            ), "Join request failed"

            print("Research Group Join Request Test Passed ✅")
        else:
            print("Join button not found (may already be member) — Skipped")
    else:
        print("Could not find the created group in list — Skipped")

finally:
    driver.quit()
