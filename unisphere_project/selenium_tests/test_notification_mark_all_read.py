import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unilink.settings")

import django
django.setup()

from django.contrib.auth import get_user_model

from notifications.models import Notification

from common import get_driver, login, BASE_URL
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

User = get_user_model()
PASSWORD = "TestPass123@#"


def ensure_user(username, role="student"):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@uap-bd.edu",
            "role": role,
            "department": "CSE",
            "university_id": f"U{abs(hash(username)) % 1000000:06d}",
        },
    )
    user.role = role
    user.set_password(PASSWORD)
    user.save()
    return user


# Setup user + 3 unread notifications
user = ensure_user("selenium_notif_user", role="student")

# Wipe old notifications for this user, then add 3 unread
Notification.objects.filter(recipient=user).delete()

for i in range(1, 4):
    Notification.objects.create(
        recipient=user,
        title=f"Selenium Notif {i}",
        message=f"Test notification number {i}",
        link="",
        is_read=False,
    )

# Sanity: 3 unread exist
unread_before = Notification.objects.filter(recipient=user, is_read=False).count()
assert unread_before == 3, f"Setup failed: expected 3 unread, got {unread_before}"

driver = get_driver()

try:
    # Step 1: Login
    login(driver, "selenium_notif_user", PASSWORD)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Step 2: Hit "mark all read" URL directly
    driver.get(f"{BASE_URL}/notifications/read-all/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    print("After mark-all-read URL:", driver.current_url)

    # Step 3: Verify all notifications are now read
    unread_after = Notification.objects.filter(recipient=user, is_read=False).count()
    read_after = Notification.objects.filter(recipient=user, is_read=True).count()

    assert unread_after == 0, (
        f"Expected 0 unread after mark-all-read, got {unread_after}"
    )
    assert read_after == 3, (
        f"Expected 3 read notifications, got {read_after}"
    )

    print("Mark All Notifications Read Test Passed ✅")

finally:
    driver.quit()
