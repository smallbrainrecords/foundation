from time import sleep
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


SHORT_WAIT_TIMEOUT = 3  # seconds
WAIT_TIMEOUT = 30  # seconds


def add_problem(driver, problem_term):
    """
    Add a todo.

    Args:
        driver (webdriver): Current driver.
        problem_term (str): Problem term to be created.
    """
    # Scroll down
    driver.execute_script('window.scrollTo(0, 600)')
    
    # Add problem tab
    add_problem_tab = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="tab-content"]/div/div[1]/div[1]/div[1]/div/div[2]/div/ul/li[3]/a')))
    
    add_problem_tab.click()

    # Type Problem term
    problem_term_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="problemTermInput"]')))

    problem_term_input.send_keys(problem_term)

    # Add problem buttom
    add_problem_buttom = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="tab-content"]/div/div[1]/div[1]/div[1]/div/div[2]/div/div/div[3]/div/div[1]/div[1]/span/button')))

    add_problem_buttom.click()

    sleep(SHORT_WAIT_TIMEOUT)

    # Submit
    alert = driver.switch_to.alert

    assert alert.text == 'Are you sure?', alert.text

    alert.accept()

    problem_term_input.clear()
    
    sleep(SHORT_WAIT_TIMEOUT)


def show_problem(driver, problem_term):
    """
    Show problem when is in manage patient page

    Args:
        driver (webdriver): Current driver.
        problem_term (str): Problem term to be selected.
    """
    
    # Scroll down
    driver.execute_script('window.scrollTo(0, 600)')
    
    # Active problems tab
    active_problems_tab = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="tab-content"]/div/div[1]/div[1]/div[1]/div/div[2]/div/ul/li[1]/a')))
    
    active_problems_tab.click()
    
    # Search in problems
    problems_list = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="tab-content"]/div/div[1]/div[1]/div[1]/div/div[2]/div/div/div[1]/div/ul')))

    problems = problems_list.find_elements_by_tag_name('li')

    for problem_li in problems:
        if problem_li.text == problem_term:
            problem_li.click()            
            break

    sleep(SHORT_WAIT_TIMEOUT)
    
    
def edit_problem_term(driver, new_problem_term):
    """
    Edit the problem term

    Args:
        driver (webdriver): Current driver.
        new_problem_term (str): New term of the problem.
    """
    # Type new problem term

    problem_term_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="problemTermInput"]')))

    problem_term_input.send_keys(new_problem_term)
    sleep(10)

    # Change problem term
    change_problem_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="main-menu"]/div[1]/div/div[1]/button')))

    change_problem_button.click()

    sleep(SHORT_WAIT_TIMEOUT)

    # Submit
    alert = driver.switch_to.alert

    assert alert.text == 'Are you sure?', alert.text

    alert.accept()

    sleep(SHORT_WAIT_TIMEOUT)


def add_problem_goal(driver, goal):
    """
    Add problem's goal.

    Args:
        driver (webdriver): Current driver.
        goal (str): Problem goal name.
    """
    # Scroll down
    driver.execute_script('window.scrollTo(0, 600)')

    # Type Problem goal
    problem_goal_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'goalNameInput')))

    problem_goal_input.send_keys(goal)
    
    # Submit
    add_goal_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/section/section[8]/div[2]/div/div/form/div/span/input')))

    add_goal_button.click()
    
    # Submit
    goal_li = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ng-app"]/div[2]/section/section[8]/div[2]/div/div/ul/li[2]')))
    
    
    assert goal_li.text.endswith(goal)
    
    sleep(SHORT_WAIT_TIMEOUT)
    
    
def view_problem_goal(driver, goal):
    """
    View problem's goal from problem page.

    Args:
        driver (webdriver): Current driver.
        goal (str): Problem goal name.
    """
    # Scroll down
    driver.execute_script('window.scrollTo(0, 850)')
    
    # Search goals
    problems_goals = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/section/section[8]/div[2]/div/div/ul')))

    goals = problems_goals.find_elements_by_tag_name('li')
    
    for goal_li in goals:
        if goal_li.text.endswith(goal):
            view_goal_button = goal_li.find_element_by_tag_name('a')
            view_goal_button.click()
            break

    sleep(SHORT_WAIT_TIMEOUT)
    
    
def add_goal_note(driver, note):
    """
    Add goal's note.

    Args:
        driver (webdriver): Current driver.
        note (str): Note to be added.
    """
    # Type Goal note
    note_input = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div[2]/textarea')))

    note_input.send_keys(note)
    
    # Submit
    add_note_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/div[2]/button')))
    
    add_note_button.click()
    
    sleep(SHORT_WAIT_TIMEOUT)
    

def update_goal_status(driver, currently_succeding, is_accomplished):
    """
    Update goal's status.

    Args:
        driver (webdriver): Current driver.
        currently_succeding (bool): Check currently_succeding option.
        is_accomplished (bool): Check is_accomplished option.
    """
    # Is Controlled checkbox
    is_controlled_checkbox = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'is_controlled_checkbox')))
    
    if is_controlled_checkbox.is_selected != currently_succeding:
        is_controlled_checkbox.click()
        
    # Is accomplished checkbox
    is_accomplished_checkbox = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'is_accomplished_checkbox')))
    
    if is_accomplished_checkbox.is_selected != is_accomplished:
        is_accomplished_checkbox.click()
    
    sleep(SHORT_WAIT_TIMEOUT)


def relate_problems(driver, problem_1, problem_2):
    """
    Create a relationship with two problem

    Args:
        driver (webdriver): Current driver.
        problem_1 (str): Problem 1
        problem_2 (str): Problem 2
    """
    # Scroll down
    driver.execute_script('window.scrollTo(0, 800)')
    
    # Activate Edit mode relationships
    edit_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ng-app"]/div[2]/section/section[6]/div[2]/div[3]/button')))
    
    edit_button.click()
    
    # Check effecting problem
    problem_2_effecting_checkbox = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'eff3')))
    
    problem_2_effecting_checkbox.click()
    
    # Check effected problem
    problem_2_effected_checkbox = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, 'effected_3')))
    
    problem_2_effected_checkbox.click()
    
    # Save relationships
    save_button = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="ng-app"]/div[2]/section/section[6]/div[2]/div[3]/button')))
    
    save_button.click()
    
    sleep(SHORT_WAIT_TIMEOUT)
    