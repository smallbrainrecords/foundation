"""Common functions of integration testing with selenium"""
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from emr.models import UserProfile


SHORT_WAIT_TIMEOUT = 3  # seconds
WAIT_TIMEOUT = 30  # seconds

ADMIN_USER = {'username': 'admin', 'first_name': 'admin_Fn', 'last_name': 'admin_Ln',
              'password': 'abc12345', 'role': 'admin', 'email': 'admin@mail.com'}
PATIENT_USER = {'username': 'patient@mail.com', 'first_name': 'patient_Fn', 'last_name': 'patient_Ln',
                'password': 'abc12345', 'role': 'patient', 'email': 'patient@mail.com'}
TEMP_PATIENT_USER = {'username': 'temp-patient@mail.com', 'first_name': 'patient_Fn-temp',
                     'last_name': 'patient_Ln-temp', 'password': 'abc12345', 'role': 'Patient', 'email': 'temp-patient@mail.com'}
PHYSICIAN_USER = {'username': 'physician@mail.com', 'first_name': 'physician_Fn',
                  'last_name': 'physician_Ln', 'password': 'abc12345', 'role': 'Physician', 'email': 'physician@mail.com'}
TEMP_PHYSICIAN_USER = {'username': 'temp-physician@mail.com', 'first_name': 'physician_Fn-temp',
                       'last_name': 'physician_Ln-temp', 'password': 'abc12345', 'role': 'Physician', 'email': 'temp-physician@mail.com'}


def build_driver():
    """Build the web driver.

    Returns:
        webdriver
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')

    return webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)


def load_data():
    """Load data into test database"""
    _create_user(ADMIN_USER)
    _create_user(PATIENT_USER)
    _create_user(PHYSICIAN_USER)


def register_patient(driver, base_url, email, password, first_name, last_name):
    """Complete a register patient form"""
    driver.get(base_url)

    # Go to login page

    login_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.LINK_TEXT, 'Login'))
    )
    login_button.click()

    # Submit available

    submit_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[2]/div/div[2]/form/div[6]/button')
                                       ))

    email_field = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[2]/div/div[2]/form/div[1]/input')
    password_field = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[2]/div/div[2]/form/div[2]/input')
    verifiy_password_field = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[2]/div/div[2]/form/div[3]/input')
    first_name_field = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[2]/div/div[2]/form/div[4]/input')
    last_name_field = driver.find_element_by_xpath(
        '/html/body/div[1]/div/div[2]/div/div[2]/form/div[5]/input')

    email_field.send_keys(email)
    password_field.send_keys(password)
    verifiy_password_field.send_keys(password)
    first_name_field.send_keys(first_name)
    last_name_field.send_keys(last_name)

    submit_button.click()

    sleep(SHORT_WAIT_TIMEOUT)


def login(driver, base_url, username, password):
    """Do a login.

    Args:
        driver: web driver.
        username (str): username of the user.
        password (str): password of the user.
    """
    driver.get(base_url)

    # Go to login page

    login_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.LINK_TEXT, 'Login'))
    )
    login_button.click()

    # Submit available

    submit_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="dvmain"]/div/div[1]/div/div[2]/form/div[3]/center/button')
                                       ))

    username_field = driver.find_element_by_name('username')
    password_field = driver.find_element_by_name('password')
    username_field.send_keys(username)
    password_field.send_keys(password)

    submit_button.click()

    sleep(SHORT_WAIT_TIMEOUT)


def approve_user(driver, username, role):
    """
    Approves an user

    Login with an admin user is required.
    """
    table = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/table')
                                       ))

    users = table.find_elements_by_tag_name('tr')
    del users[0]  # Remove table headers

    user_found = False

    if len(users) > 1:
        # Search in users waiting approval.
        for idx, user in enumerate(users):
            user = user.text.split()

            if user[2] == username:
                user_found = True

                # Assign role
                select_role = Select(driver.find_element_by_xpath(
                    '//*[@id="ng-app"]/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr/td[3]/select'.format(idx+1)))
                select_role.select_by_visible_text(role)

                # Approve
                driver.find_element_by_xpath(
                    '/html/body/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr/td[4]/button[1]'.format(idx+1)).click()
                break

    elif len(users) == 1:
        user = users[0].text.split()

        if user[2] == username:
            user_found = True
            # Assign role
            select_role = Select(driver.find_element_by_xpath(
                '//*[@id="ng-app"]/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr/td[3]/select'))

            select_role.select_by_visible_text(role)

            # Approve
            driver.find_element_by_xpath(
                '/html/body/div[2]/div/div[2]/div/div[2]/div[2]/div[2]/table/tbody/tr/td[4]/button[1]').click()

    sleep(SHORT_WAIT_TIMEOUT)

    assert user_found, 'User to be approved is not found. Username -> {}'.format(
        username)


def manage_patient(driver, username):
    """Go to manage a patient.

    Args:
        driver : web driver
        username (str): username of the patient.
    """
    table = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'table')
                                       ))

    users = table.find_elements_by_tag_name('tr')
    del users[0]  # Remove table headers

    for idx, user in enumerate(users):
        user = user.text.split()

        if user[2] == username:
            driver.find_element_by_xpath(
                '//*[@id="ng-app"]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr[{}]/td[7]/a[2]'.format(idx+1)).click()
            break

    sleep(SHORT_WAIT_TIMEOUT)


def add_todo(driver, username, title, physician_full_name=None):
    """Add a todo.

    Args:
        username (str): Username of the patient.
        title (str): title of the todo.
    """
    # Add title

    todo = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'todoNameInput')
                                       ))
    todo.send_keys(title)
    driver.find_element_by_xpath(
        '//*[@id="tab-content"]/div/div[1]/div[1]/div[2]/div/div[2]/form/div/span/button').click()

    # Add without date
    add_without_date_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ngdialog1"]/div[2]/div/div[2]/button[2]')
                                       ))

    add_without_date_button.click()

    # Submit

    submit_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[8]/div[2]/form/button')
                                       ))
    # Tag physician

    if physician_full_name:

        tag_dialog_div = driver.find_element_by_xpath(
            '//*[@id="ngdialog2"]/div[2]')

        physicians = tag_dialog_div.find_elements_by_tag_name('a')

        for physician in physicians:
            if physician.text == physician_full_name:
                physician.click()
                break

    submit_button.click()

    sleep(SHORT_WAIT_TIMEOUT)


def edit_patient(driver, username):
    """Go to edit patient page.

    Args:
        username (str): username of the patient.
    """
    table = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'table')
                                       ))

    users = table.find_elements_by_tag_name('tr')
    del users[0]  # Remove table headers

    for idx, user in enumerate(users):
        user = user.text.split()

        if user[2] == username:
            driver.find_element_by_xpath(
                '//*[@id="ng-app"]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr[{}]/td[7]/a[1]'.format(idx+1)).click()
            break

    sleep(SHORT_WAIT_TIMEOUT)


def assing_physician_to_patient(driver, patient_username, physician_username):
    """Assing a physician with a patient.

    Args:
        patient_username (str): username of the patient.
        physician_username (str): username of the physician.

    Edit patient page is required.
    """

    # Select physician
    select_physician = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id="physiciansInfo"]/div[2]/form/div[1]/select')
                                       ))
    # Use Select wrapper
    select_physician = Select(select_physician)

    for option in select_physician.options:
        if option.text.endswith(physician_username):
            select_physician.select_by_visible_text(option.text)

            # Assing
            driver.find_element_by_xpath(
                '//*[@id="physiciansInfo"]/div[2]/form/div[2]/input').click()
            break

    sleep(SHORT_WAIT_TIMEOUT)


def register_user_by_admin(driver, first_name, last_name, username, email, role, password):
    """Add an user using an admin account. 

    Args:
        first_name (str): first name of the user.
        last_name (str): last name of the user.
        username (str): username of the user.
        email (str): email of the user.
        role (str): role of the user.
        password (str): password of the user.
    """
    # Go to Add user.

    add_user_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH,
                                        '//*[@id="ng-app"]/div[2]/div/div[1]/div/div[2]/a[1]')
                                       ))
    add_user_button.click()

    # Write Essential information.

    submit_buttom = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ng-app"]/div[2]/div/div/form/div[14]/input')
                                       ))

    first_name_field = driver.find_element_by_id('first_name')
    first_name_field.send_keys(first_name)

    last_name_field = driver.find_element_by_id('last_name')
    last_name_field.send_keys(last_name)

    username_field = driver.find_element_by_id('username')
    username_field.send_keys(username)

    email_field = driver.find_element_by_id('email')
    email_field.send_keys(email)

    select_role = Select(driver.find_element_by_xpath(
        '//*[@id="ng-app"]/div[2]/div/div/form/div[5]/select'))
    select_role.select_by_visible_text(role)

    password_field = driver.find_element_by_xpath(
        '//*[@id="ng-app"]/div[2]/div/div/form/div[6]/input')
    password_field.send_keys(password)

    verify_password_field = driver.find_element_by_xpath(
        '//*[@id="ng-app"]/div[2]/div/div/form/div[7]/input')
    verify_password_field.send_keys(password)

    # Submit
    submit_buttom.click()

    sleep(SHORT_WAIT_TIMEOUT)

    # Go home

    alert = driver.switch_to.alert

    assert alert.text == 'User is created', alert.text

    sleep(SHORT_WAIT_TIMEOUT)


def _create_user(user_data):
    """
    Create an user into database
    """
    user = User(username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'])
    user.set_password(user_data['password'])
    user.save()

    user_profile = UserProfile(
        user=user,
        role=user_data['role'],
        summary='summary',
        sex='male',
        date_of_birth=None,
        phone_number='8888888')

    user_profile.save()
