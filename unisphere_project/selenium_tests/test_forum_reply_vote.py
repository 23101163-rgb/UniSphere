import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common import get_driver, login, BASE_URL

User = get_user_model()


def ensure_user(username, password, role="student", email=None, **extra):
    email = email or f"{username}@uap-bd.edu"
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "role": role,
            "department": "CSE",
            "university_id": extra.pop("university_id", f"U{abs(hash(username)) % 1000000:06d}"),
        },
    )
    user.email = email
    user.role = role
    user.department = extra.pop("department", "CSE")
    if not user.university_id:
        user.university_id = f"U{abs(hash(username)) % 1000000:06d}"
    for key, value in extra.items():
        setattr(user, key, value)
    user.set_password(password)
    user.save()
    return user


def wait_page_ready(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return wait


from forum.models import Category, Thread, Reply, Vote

PASSWORD = "TestPass123@#"

author = ensure_user(
    username="selenium_forum_author",
    password=PASSWORD,
    role="student",
    email="selenium_forum_author@uap-bd.edu",
    first_name="Forum",
    last_name="Author",
)

voter = ensure_user(
    username="selenium_forum_voter",
    password=PASSWORD,
    role="student",
    email="selenium_forum_voter@uap-bd.edu",
    first_name="Forum",
    last_name="Voter",
)

category, _ = Category.objects.get_or_create(
    slug="selenium-testing",
    defaults={
        "name": "Selenium Testing",
        "description": "Forum category for Selenium tests",
    },
)

Thread.objects.filter(title="Selenium Forum Reply Vote Thread").delete()

thread = Thread.objects.create(
    title="Selenium Forum Reply Vote Thread",
    content="Thread for testing reply and vote.",
    category=category,
    author=author,
)

Reply.objects.filter(thread=thread, author=voter).delete()
Vote.objects.filter(thread=thread, user=voter).delete()

driver = get_driver()
wait = WebDriverWait(driver, 10)

try:
    login(driver, "selenium_forum_voter", PASSWORD)

    driver.get(f"{BASE_URL}/forum/thread/{thread.pk}/")
    wait_page_ready(driver)

    content = wait.until(EC.presence_of_element_located((By.NAME, "content")))
    content.clear()
    content.send_keys("This is a Selenium reply.")

    driver.find_element(By.TAG_NAME, "form").submit()
    wait_page_ready(driver)

    assert Reply.objects.filter(thread=thread, author=voter, content__icontains="Selenium reply").exists(), "Forum reply was not saved"

    driver.get(f"{BASE_URL}/forum/thread/{thread.pk}/upvote/")
    wait_page_ready(driver)

    assert Vote.objects.filter(thread=thread, user=voter, vote_type="up").exists(), "Thread upvote was not saved"

    print("Forum Reply/Vote Test Passed ✅")

finally:
    driver.quit()

