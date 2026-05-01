from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    # Step 1: Login
    login(driver, "ABaki", "amibaki123@#")

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Go to thesis list
    driver.get(f"{BASE_URL}/thesis/")

    wait.until(
        EC.url_contains("/thesis")
    )

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    current_url = driver.current_url.lower()

    assert "/thesis" in current_url, (
        f"Thesis page did not load.\nURL: {driver.current_url}"
    )

    print("Thesis Archive Page Loaded ✅")

    # Step 3: Search if search field exists
    try:
        search_field = driver.find_element(By.NAME, "q")
        search_field.clear()
        search_field.send_keys("AI")
        search_field.submit()

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("Thesis Search Executed ✅")

    except Exception:
        print("No search field found — Skipped search step")

    # Step 4: Open first thesis detail if exists
    wait.until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    thesis_links = driver.execute_script("""
        return Array.from(document.querySelectorAll('a'))
            .map(a => a.href)
            .filter(href => href.includes('/thesis/'))
            .filter(href => {
                let parts = href.replace(/\\/$/, '').split('/');
                return /^\\d+$/.test(parts[parts.length - 1]);
            });
    """)

    if thesis_links:
        driver.get(thesis_links[0])

        wait.until(
            EC.url_contains("/thesis/")
        )

        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print("Thesis Detail Page Loaded ✅")
    else:
        print("No thesis entries found to open — Skipped detail step")

    # Step 5: Go to mentor list
    driver.get(f"{BASE_URL}/thesis/mentors/")

    wait.until(
        EC.url_contains("/thesis/mentors")
    )

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    assert "/thesis/mentors" in driver.current_url.lower(), (
        f"Mentor list page did not load.\nURL: {driver.current_url}"
    )

    print("Mentor List Page Loaded ✅")
    print("Thesis Browse Test Passed ✅")

finally:
    driver.quit()
