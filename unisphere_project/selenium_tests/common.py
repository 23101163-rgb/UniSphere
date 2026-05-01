import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.environ.get("SELENIUM_BASE_URL", "http://127.0.0.1:8000")

# Provided Selenium test users
STUDENT_USERNAME = "Adika"
STUDENT_PASSWORD = "amiadika123@#"
STUDENT_EMAIL = "23101162@uap-bd.edu"

TEACHER_USERNAME = "NMK"
TEACHER_PASSWORD = "amiarnob123@#"
TEACHER_EMAIL = "arnob@uap-bd.edu"

ADMIN_USERNAME = "ARaiyan"
ADMIN_PASSWORD = "amiraiyan123@#"
ADMIN_EMAIL = "raiyan@uap-bd.edu"


def _setup_django_if_possible():
    """Allow script-style Selenium tests to create/update the required accounts."""
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unisphere.settings")

        import django
        django.setup()
        return True
    except Exception:
        return False


def ensure_core_test_users():
    """Create/update the three fixed users requested for Selenium testing."""
    if not _setup_django_if_possible():
        return

    try:
        from django.contrib.auth import get_user_model
        from accounts.models import ClubMembership, TeacherCourseAssignment

        User = get_user_model()

        student, _ = User.objects.get_or_create(
            username=STUDENT_USERNAME,
            defaults={
                "email": STUDENT_EMAIL,
                "university_id": "23101162",
                "role": "student",
                "first_name": "Adika",
                "last_name": "Sulatana",
                "department": "CSE",
            },
        )
        student.email = STUDENT_EMAIL
        student.university_id = "23101162"
        student.role = "student"
        student.first_name = "Adika"
        student.last_name = "Sulatana"
        student.department = "CSE"
        student.is_club_member = True
        student.is_club_verified = True
        student.club_name = "robotics_club"
        student.club_position = "member"
        student.set_password(STUDENT_PASSWORD)
        student.save()

        ClubMembership.objects.update_or_create(
            user=student,
            club_name="robotics_club",
            defaults={
                "club_position": "member",
                "is_verified": True,
                "authorized_to_post": True,
            },
        )

        teacher, _ = User.objects.get_or_create(
            username=TEACHER_USERNAME,
            defaults={
                "email": TEACHER_EMAIL,
                "university_id": "920001",
                "role": "teacher",
                "first_name": "NMK",
                "last_name": "Arnob",
                "department": "CSE",
            },
        )
        teacher.email = TEACHER_EMAIL
        teacher.university_id = "920001"
        teacher.role = "teacher"
        teacher.first_name = "NMK"
        teacher.last_name = "Arnob"
        teacher.department = "CSE"
        teacher.teacher_course_name = "CSE101"
        teacher.set_password(TEACHER_PASSWORD)
        teacher.save()

        for semester, course in [
            ("1.1", "CSE101"),
        ]:
            TeacherCourseAssignment.objects.update_or_create(
                teacher=teacher,
                semester=semester,
                course_name=course,
                defaults={},
            )

        admin, _ = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={
                "email": ADMIN_EMAIL,
                "university_id": "900001",
                "role": "admin",
                "first_name": "A",
                "last_name": "Raiyan",
                "department": "CSE",
            },
        )
        admin.email = ADMIN_EMAIL
        admin.university_id = "900001"
        admin.role = "admin"
        admin.first_name = "A"
        admin.last_name = "Raiyan"
        admin.department = "CSE"
        admin.set_password(ADMIN_PASSWORD)
        admin.save()

    except Exception as exc:
        print(f"Core Selenium user setup skipped/failed: {exc}")


# Run once whenever a Selenium script imports common.py.
ensure_core_test_users()


def get_driver():
    options = Options()
    if os.environ.get("SELENIUM_HEADLESS", "0") == "1":
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def login(driver, username, password):
    ensure_core_test_users()

    driver.get(f"{BASE_URL}/accounts/login/")

    wait = WebDriverWait(driver, 12)

    wait.until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys(username)

    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys(password)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    wait.until(
        EC.url_contains("/accounts/dashboard")
    )

