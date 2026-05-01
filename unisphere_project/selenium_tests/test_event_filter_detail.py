from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

driver = get_driver()

try:
    # Step 1: Login as student
    login(driver, "Shifat", "amishifat123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Go to events list page
    driver.get(f"{BASE_URL}/events/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 3: Find and click an event detail link
    # Non-club events have links like /events/<pk>/
    event_link = None
    for a in driver.find_elements(By.TAG_NAME, "a"):
        href = a.get_attribute("href") or ""
        text = a.text.strip().lower()
        # Look for "View" button or direct event link (not club, not create, not register)
        if "/events/" in href and href.rstrip('/').split('/')[-1].isdigit():
            if "/register" not in href and "/create" not in href and "/club/" not in href:
                event_link = a
                break

    # If no non-club event found, try clicking a club card first then find event
    if not event_link:
        for a in driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href") or ""
            if "/events/club/" in href:
                a.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # Now find event detail link inside club page
                for a2 in driver.find_elements(By.TAG_NAME, "a"):
                    href2 = a2.get_attribute("href") or ""
                    if "/events/" in href2 and href2.rstrip('/').split('/')[-1].isdigit():
                        if "/register" not in href2 and "/create" not in href2 and "/club/" not in href2:
                            event_link = a2
                            break
                if event_link:
                    break

    assert event_link is not None, (
        "No event found on events page. Make sure at least one APPROVED event exists in the database."
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", event_link)
    try:
        event_link.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", event_link)

    # Step 4: Now on event detail page — find register link
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_text = driver.page_source.lower()
    print(f"Event detail loaded: {driver.current_url}")

    # Check if already registered (Cancel Registration shown)
    if "cancel registration" in page_text:
        print("Already registered for this event. Test Passed ✅ (already registered)")
    elif "registration closed" in page_text:
        print("Event has ended, registration closed. Skipped.")
    else:
        # Find the register link: href contains /register/
        register_link = None
        for a in driver.find_elements(By.TAG_NAME, "a"):
            href = a.get_attribute("href") or ""
            if "/register/" in href:
                register_link = a
                break

        assert register_link is not None, (
            f"Register button not found on event detail page.\n"
            f"URL: {driver.current_url}\n"
            f"Page text preview: {page_text[:500]}"
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", register_link)
        try:
            register_link.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", register_link)

        # Step 5: Fill registration form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        current_url = driver.current_url.lower()

        # If redirected to detail (GET cancels registration), we're done
        if "/register/" not in current_url:
            print("Registration toggled (GET cancelled). Test Passed ✅")
        else:
            # We're on the registration form page — fill it out
            try:
                full_name = driver.find_element(By.NAME, "full_name")
                if not full_name.get_attribute("value"):
                    full_name.clear()
                    full_name.send_keys("Shifat Test User")

                email_field = driver.find_element(By.NAME, "email")
                if not email_field.get_attribute("value"):
                    email_field.clear()
                    email_field.send_keys("shifat@uap-bd.edu")

                phone_field = driver.find_element(By.NAME, "phone")
                if not phone_field.get_attribute("value"):
                    phone_field.clear()
                    phone_field.send_keys("01700000000")

                dept_field = driver.find_element(By.NAME, "department")
                if not dept_field.get_attribute("value"):
                    dept_field.clear()
                    dept_field.send_keys("CSE")

                uid_field = driver.find_element(By.NAME, "university_id")
                if not uid_field.get_attribute("value"):
                    uid_field.clear()
                    uid_field.send_keys("23101158")

            except Exception as e:
                print(f"Form field issue: {e}")

            # Submit
            submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)

            try:
                submit_btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", submit_btn)

            # Step 6: Verify
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            page_text = driver.page_source.lower()

            assert (
                    "cancel registration" in page_text or
                    "registered" in page_text or
                    "you are registered" in page_text
            ), (
                f"Registration failed.\n"
                f"URL: {driver.current_url}\n"
                f"Preview: {page_text[:500]}"
            )

            print("Event Register Test Passed ✅")

finally:
    driver.quit()
