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
