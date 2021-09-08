"""
Common functions of integration testing with selenium
"""
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from django.contrib.auth.models import User
from emr.models import UserProfile
from emr.models import Encounter
import os
import filecmp
from selenium.webdriver.remote.webelement import WebElement


SHORT_WAIT_TIMEOUT = 3  # seconds
WAIT_TIMEOUT = 30  # seconds
ENCOUNTER_WAIT_TIMEOUT = 10  # seconds
PATIENT_ID = 2 # id of patient on DB
PHYSICIAN_ID = 1 # id of physician on DB
PATH_TO_AUDIO = 'test/test_encounter/audioSample1.mp3'
PATH_TO_DOCUMENT = 'test/test_documents/documentSample1.txt'
PATH_TO_DOCUMENT_MEDIA = 'media/documents/documentSample1.txt'
PATH_TO_DOCUMENT_FOLDER = 'media/documents'

# JavaScript: HTML5 File drop
# source            : https://gist.github.com/florentbr/0eff8b785e85e93ecc3ce500169bd676
# param1 WebElement : Drop area element
# param2 Double     : Optional - Drop offset x relative to the top/left corner of the drop area. Center if 0.
# param3 Double     : Optional - Drop offset y relative to the top/left corner of the drop area. Center if 0.
# return WebElement : File input
JS_DROP_FILES = "var c=arguments,b=c[0],k=c[1];c=c[2];for(var d=b.ownerDocument||document,l=0;;){var e=b.getBoundingClientRect(),g=e.left+(k||e.width/2),h=e.top+(c||e.height/2),f=d.elementFromPoint(g,h);if(f&&b.contains(f))break;if(1<++l)throw b=Error('Element not interactable'),b.code=15,b;b.scrollIntoView({behavior:'instant',block:'center',inline:'center'})}var a=d.createElement('INPUT');a.setAttribute('type','file');a.setAttribute('multiple','');a.setAttribute('style','position:fixed;z-index:2147483647;left:0;top:0;');a.onchange=function(b){a.parentElement.removeChild(a);b.stopPropagation();var c={constructor:DataTransfer,effectAllowed:'all',dropEffect:'none',types:['Files'],files:a.files,setData:function(){},getData:function(){},clearData:function(){},setDragImage:function(){}};window.DataTransferItemList&&(c.items=Object.setPrototypeOf(Array.prototype.map.call(a.files,function(a){return{constructor:DataTransferItem,kind:'file',type:a.type,getAsFile:function(){return a},getAsString:function(b){var c=new FileReader;c.onload=function(a){b(a.target.result)};c.readAsText(a)}}}),{constructor:DataTransferItemList,add:function(){},clear:function(){},remove:function(){}}));['dragenter','dragover','drop'].forEach(function(a){var b=d.createEvent('DragEvent');b.initMouseEvent(a,!0,!0,d.defaultView,0,0,0,g,h,!1,!1,!1,!1,0,null);Object.setPrototypeOf(b,null);b.dataTransfer=c;Object.setPrototypeOf(b,DragEvent.prototype);f.dispatchEvent(b)})};d.documentElement.appendChild(a);a.getBoundingClientRect();return a;"

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
TEMP_NURSE_USER = {'username': 'temp-nurse@mail.com', 'first_name': 'nurse_Fn-temp',
                       'last_name': 'nurse_Ln-temp', 'password': 'abc12345', 'role': 'Nurse', 'email': 'temp-nurse@mail.com'}


def build_driver():
    """
    Build the web driver.

    Returns:
        webdriver
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-popup-blocking")

    return webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)


def drop_files(element, files, offsetX=0, offsetY=0):
    """
    Drops file on web element

    Args:
        element (web element): web element to drop files in.
        files: files to drop into web element.
        offsetX (int): x position relative to the top/left corner of the drop area. Center if 0.
        offsetY (int): y position relative to the top/left corner of the drop area. Center if 0.
    """

    driver = element.parent
    is_local = not driver._is_remote or '127.0.0.1' in driver.command_executor._url
    paths = []
    
    # ensure files are present, and upload to the remote server if session is remote
    for file in (files if isinstance(files, list) else [files]) :
        if not os.path.isfile(file) :
            raise IOError
        paths.append(file if is_local else element._upload(file))
    
    value = '\n'.join(paths)
    elm_input = driver.execute_script(JS_DROP_FILES, element, offsetX, offsetY)
    elm_input._execute('sendKeysToElement', {'value': [value], 'text': value})

#Make future web drivers able to use drop_files method
WebElement.drop_files = drop_files


def load_data():
    """
    Load data into test database
    """
    _create_user(ADMIN_USER)
    _create_user(PATIENT_USER)
    _create_user(PHYSICIAN_USER)
    
    
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

    # Tag physician
    if physician_full_name:
        tag_dialog_div = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="ngdialog2"]/div[2]')
                                           ))
        physicians = tag_dialog_div.find_elements_by_tag_name('a')

        for physician in physicians:
            if physician.text == physician_full_name:
                physician.click()
                break

    # Submit
    submit_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[8]/div[2]/form/button')
                                       ))

    submit_button.click()

    sleep(SHORT_WAIT_TIMEOUT)


def register_patient(driver, base_url, email, password, first_name, last_name):
    """
    Complete a register patient form
    
    Args:
        driver: web driver.
        base_url: live server url
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
    """
    Do a login.

    Args:
        driver: web driver.
        base_url: live server url
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
    Description:
        Approves an user
    
    Args:
        driver: web driver.
        username (str): username of the user.
        role (str): role of the user.
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
        driver: web driver
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

    
def edit_patient(driver, username):
    """Go to edit patient page.

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
                '//*[@id="ng-app"]/div[2]/div/div[2]/div[1]/div[2]/table/tbody/tr[{}]/td[7]/a[1]'.format(idx+1)).click()
            break

    sleep(SHORT_WAIT_TIMEOUT)


def assing_physician_to_patient(driver, patient_username, physician_username):
    """Assing a physician with a patient.

    Args:
        driver : web driver
        patient_username (str): username of the patient.
        physician_username (str): username of the physician.
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
        driver : web driver
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

    Args:
        user_data (tuple): tuple of user data
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


def get_encounter_audio_route_DB(physician_id,patient_id):
    """
    Gets part of the route of an audio encounter for a user from the DB

    Args:
        physician_id (int): db id of physician
        patient_id (int): db id of patient
    """
    encounter=Encounter.objects.get(physician=PHYSICIAN_ID,patient =PATIENT_ID)
    
    return encounter.audio

          
def _get_complete_media_route(cwd,audio_route, only_media_folder):
    """
    Gets the complete audio encounter route to on the media folder

    Args:
        cwd: current working directory
        audio_route: db stored audio route per encounter
    """
    new_audio_route = 'media'
    if only_media_folder == 2:
        new_audio_route = 'media/' + str(audio_route)
    
    else:
        str_audio_route = str(audio_route)
        list_audio_route = str_audio_route.split('/')   
        new_audio_route = new_audio_route + '/' + list_audio_route[0]

    complete_audio_media_route = os.path.join (cwd,new_audio_route)
    return complete_audio_media_route


def assert_audio_encounter(cwd,audio_route):
    """
    Verify if the audio sample is on the media file
    Args:
        cwd: current working directory
        audio_route: db stored audio route per encounter
    """
    only_media_folder = 2
    return os.path.isfile(_get_complete_media_route(cwd,audio_route,only_media_folder))


def add_encounter(driver,live_server_url):
    """
    Creates an encounter while managing a patient on a admin account
    Args:
        driver : web driver
        live_server_url: url of test
    """
    start_encounter_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="encounter-box"]/div[1]/button')))
    
    # Start encounter
    start_encounter_button.click()
    sleep(ENCOUNTER_WAIT_TIMEOUT)

    # Stop encounter
    driver.find_element_by_xpath(
        '//*[@id="encounter-box"]/div[2]/div/div[1]/div[1]/button[1]').click()
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Refresh the page
    driver.refresh()
    
    # Go to encounter
    driver.get('{}/u/patient/manage/2/#/encounter/1'.format(live_server_url))
    sleep(SHORT_WAIT_TIMEOUT)


def delete_document_from_media (cwd):
    """
    Deletes document from media file
    Args:
        cwd: current working directory
    """
    complete_document_media_route = os.path.join (cwd,PATH_TO_DOCUMENT_MEDIA)
    os.remove(complete_document_media_route)


def delete_document_media_folder(cwd):
    """
    Deletes document media folder
    Args:
        cwd: current working directory
    """
    PATH_TO_DOCUMENT_FOLDER
    complete_document_media_folder_route = os.path.join (cwd,PATH_TO_DOCUMENT_FOLDER)
    if len(os.listdir(complete_document_media_folder_route) ) == 0:
        os.rmdir(complete_document_media_folder_route)


def delete_audio_from_media(cwd,audio_route):
    """
    Deletes an audio from media folder
    Args:
        cwd: current working directory
        audio_route: db stored audio route per encounter
    """
    if(str(audio_route) != ''):
        only_media_folder = 2
        complete_audio_media_route = _get_complete_media_route(cwd,audio_route,only_media_folder)
        os.remove(complete_audio_media_route)


def delete_test_patient_media_folder(cwd,audio_route):
    """
    Deletes a patient audio folder from media folder
    Args:
        cwd: current working directory
        audio_route: db stored audio route per encounter
    """
    only_media_folder = 1
    complete_audio_media_route = _get_complete_media_route(cwd,audio_route,only_media_folder)
    if len(os.listdir(complete_audio_media_route) ) == 0:
        os.rmdir(complete_audio_media_route)


def assert_audio_conversion(cwd,audio_route):
    """
    Verify if audio conversion was successful
    Args:
        cwd: current working directory
        audio_route: db stored audio route per encounter
    """
    only_media_folder = 2
    complete_audio_media_route = _get_complete_media_route(cwd,audio_route,only_media_folder)
    complete_audio_test_route= os.path.join (cwd,PATH_TO_AUDIO)
    return filecmp.cmp(complete_audio_media_route,complete_audio_test_route,shallow=False)


def assert_add_document(cwd):
    """
    Verify if add document was successful
    Args:
        cwd: current working directory
    """
    complete_document_media_route = os.path.join (cwd,PATH_TO_DOCUMENT_MEDIA)
    complete_document_test_route= os.path.join (cwd,PATH_TO_DOCUMENT)
    return filecmp.cmp(complete_document_media_route,complete_document_media_route,shallow=False)


def upload_audio(driver,cwd):
    """
    Creates an encounter while managing a patient on an admin account
    Args:
        driver : web driver
        cwd: current working directory
    """
    # Expand driver window
    driver.maximize_window()
    
    # Start encounter
    start_encounter_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="encounter-box"]/div[1]/button')))
    start_encounter_button.click()
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Go to encounter info while encounter is active
    view_encounter_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="encounter-box"]/div[2]/div/div[1]/div[1]/button[2]')))
    sleep(SHORT_WAIT_TIMEOUT)
    view_encounter_button.click()
    sleep(SHORT_WAIT_TIMEOUT)

    # Stop encounter
    stop_encounter_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="encounter-box"]/div[2]/div/div[1]/div[1]/button[1]')))
    stop_encounter_button.click()
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Delete encounter
    audio_route = get_encounter_audio_route_DB(PHYSICIAN_ID,PATIENT_ID)
    delete_audio_from_media(cwd,audio_route)

    # Upload audio
    upload_audio_input = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.ID, 'audio_file')))
    
    # Find route to audio on test_encounters
    complete_audio_test_route= os.path.join (cwd,PATH_TO_AUDIO)
    
    # Upload audio file
    upload_audio_input.send_keys(complete_audio_test_route)
    sleep(SHORT_WAIT_TIMEOUT)
    submit_audio_upload_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="ng-app"]/div[2]/section[2]/div/div[2]/div[2]/form/div[2]/button'))) 
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Submit audio upload file
    driver.execute_script("arguments[0].scrollIntoView();", submit_audio_upload_button)
    sleep(SHORT_WAIT_TIMEOUT)
    driver.execute_script("arguments[0].click();", submit_audio_upload_button)
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Refresh the page
    driver.refresh()  
    sleep(SHORT_WAIT_TIMEOUT)


def add_document(driver,cwd):
    """
    Creates an encounter while managing a patient on an admin account
    
    Args:
        driver : web driver
        cwd: current working directoryr
    """
    # Start encounter
    data_tab_button = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="patient-profile-header"]/div[1]/ul/li[3]/a')))
    
    # Go to add document route
    sleep(SHORT_WAIT_TIMEOUT)
    driver.execute_script('arguments[0].scrollIntoView();', data_tab_button)
    sleep(SHORT_WAIT_TIMEOUT)
    driver.execute_script("arguments[0].click();", data_tab_button)
    sleep(SHORT_WAIT_TIMEOUT)
    
    # Drop a single file
    dropzone = WebDriverWait(driver, 
        WAIT_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, 
        '//*[@id="tab-content"]/div/div[3]/div/div/div/div[2]/div[1]'))) 
    sleep(SHORT_WAIT_TIMEOUT)
    complete_document_test_route= os.path.join (cwd,PATH_TO_DOCUMENT)
    sleep(SHORT_WAIT_TIMEOUT) 
    dropzone.drop_files(complete_document_test_route)
    sleep(SHORT_WAIT_TIMEOUT)    


def assing_physician_to_patient(driver, patient_username, physician_username):
    """Assing a physician with a patient.
    Args:
        patient_username (str): username of the patient.
        physician_username (str): username of the physician.
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
