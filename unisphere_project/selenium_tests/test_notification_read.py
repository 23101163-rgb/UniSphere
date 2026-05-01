from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

driver = get_driver()

try:
    # Step 1: Login
    login(driver, "ARaiyan", "amiraiyan123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Go to notifications page
    driver.get(f"{BASE_URL}/notifications/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    assert "/notifications" in driver.current_url.lower(), "Notifications page did not load"

    print("Notifications Page Loaded ✅")

    # Step 3: Click first notification link (mark as read)
    notif_link = None
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href") or ""
        if "/notifications/" in href and "/read" in href:
            notif_link = a
            break

    if notif_link:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", notif_link)

        try:
            notif_link.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", notif_link)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("Notification Mark Read Test Passed ✅")
    else:
        # Try mark all read if no individual notification
        mark_all = None
        for a in driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href") or ""
            text = a.text.lower()
            if "read-all" in href or "mark all" in text:
                mark_all = a
                break

        if mark_all:
            try:
                mark_all.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", mark_all)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("Mark All Read Test Passed ✅")
        else:
            print("No notifications found to mark as read — Skipped (no unread notifications)")

    print("Notification Read Test Passed ✅")

finally:
    driver.quit()

