from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = get_driver()

try:
    # Step 1: Login as a student
    login(driver, "Adika", "amiadika123@#")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Navigate to dashboard explicitly
    driver.get(f"{BASE_URL}/accounts/dashboard/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    current_url = driver.current_url.lower()
    page_text = driver.page_source.lower()

    print("Dashboard URL:", driver.current_url)

    # Step 3: Should be on dashboard, not redirected to login
    assert "/accounts/dashboard" in current_url, (
        f"Did not land on dashboard.\nURL: {driver.current_url}"
    )
    assert "/login" not in current_url, "Got redirected back to login"

    # Step 4: Dashboard should show key navigation/section keywords
    expected_keywords = ["dashboard", "materials", "events", "jobs", "forum"]
    found = [kw for kw in expected_keywords if kw in page_text]

    assert len(found) >= 3, (
        f"Dashboard missing expected sections. Found only: {found}\n"
        f"Preview: {page_text[:1000]}"
    )

    # Step 5: User should be logged in (Logout link visible)
    try:
        driver.find_element(By.LINK_TEXT, "Logout")
        logout_visible = True
    except Exception:
        logout_visible = "logout" in page_text

    assert logout_visible, "Logout link/text not visible — user may not be logged in"

    print(f"Dashboard Load Test Passed ✅ (found sections: {found})")

finally:
    driver.quit()

