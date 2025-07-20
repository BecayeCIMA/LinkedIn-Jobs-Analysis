import os
import re
import time
from retry import  retry
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class Scraper:

    delay = 3
    # tries = 3

    def __init__(self, delay=3):
        """
        Initialize the scraper.

        Parameters
        ----------
        delay: int
            The delay between each action. Useful when the internet connection is unstable.
        """
        self.delay = delay
        self.driver = webdriver.Chrome()
        self.print_colors = {'WARNING': '\033[93m', 'ERROR': '\033[91m'}


    def login(self):
        """
        Log in to linkedin.com using the given email and password
        """
        print("Logging in...")
        # Set credentials
        load_dotenv()
        email = os.getenv('EMAIL')
        password = os.getenv('PASSWORD')

        # If email or password is not set
        if email is None or password is None:
            raise ValueError("Either email or password is not set. Please update the '.env' file.")
        
        # Login to linkedin
        self.driver.get('https://www.linkedin.com/login')
        self.wait_till_element_ready(By.ID, "username")
        self.wait_till_element_ready(By.ID, "password")
        self.driver.find_element(By.ID, "username").send_keys(email)
        self.driver.find_element(By.ID, "password").send_keys(password, Keys.ENTER)


    @retry(TimeoutException, delay=delay) #, tries=tries)
    def wait_till_element_ready(self, by, selector):
        """
        Wait for a given element to be ready.
        Useful when the element is not loaded yet and you want to wait for it to be loaded.

        Parameters
        ----------
        by: selenium.webdriver.common.by.By
            The selector strategy. E.g.: By.ID, By.CLASS_NAME, etc.
        selector: 
            The CSS selector. Can be 'class name', 'id', etc.
        """
        WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((by, selector)))
        # time.sleep(self.delay)


    def search_jobs(self, position, location):
        """
        Search jobs on LinkedIn.
        This method enters the position and location into the search bars
        and returns the pagination buttons. These button are used to navigate through each page.

        Returns
        -------
        pagination_buttons: list
            A list of pagination buttons. These buttons are used to navigate through each page.
        """
        print("Searching for jobs: %s in %s" % (position, location))
        self.driver.get("https://www.linkedin.com/jobs/")

        # find the two search boxes: position and location
        self.wait_till_element_ready(By.CLASS_NAME, "jobs-search-box__text-input")
        search_bars = self.driver.find_elements(By.CLASS_NAME, "jobs-search-box__text-input")

        print(f"Found {len(search_bars)} search bars")
        # print(search_bars)

        # Enter job position in the search  by keyword bar
        search_by_keyword_bar = search_bars[0]
        search_by_keyword_bar.clear()                         # clear existing text
        search_by_keyword_bar.send_keys(position)

        # Enter job location in the search by location bar
        search_by_location_bar = search_bars[3]
        search_by_location_bar.clear()                        # clear existing text
        search_by_location_bar.send_keys(location, Keys.RETURN)



    def scroll_all_jobs(self):
        """
        Scrolls the job list container to load all lazy-loaded job cards.
        """
        print("Scrolling all job listings...")
        # Constants
        SCROLL_CONTAINER_XPATH = '//ul[li[@data-occludable-job-id]]'
        # JOB_LIST_CSS      = 'ul[class*="scaffold-layout__list"]'
        JOB_CARD_SELECTOR = 'li[data-occludable-job-id]'

        # scroll_container = self.driver.find_element(By.CSS_SELECTOR, JOB_LIST_CSS)
        scroll_container = self.driver.find_element(By.XPATH, SCROLL_CONTAINER_XPATH)

        prev_count = -1
        while True:
            # scroll right to the bottom in one go
            self.driver.execute_script(
                "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                scroll_container
            )
            time.sleep(self.delay)

            # see how many job cards are now in the DOM
            current_count = len(self.driver.find_elements(
                By.CSS_SELECTOR, JOB_CARD_SELECTOR
            ))
            print(f"  → {current_count} cards loaded so far…")

            # stop once no new cards appear
            if current_count == prev_count:
                print("Reached bottom of job list.")
                break
            prev_count = current_count


    def get_current_page_jobs(self):
        """
        Click on each job on the current page and extract its information:
        position, company, location, work mode, skills, description.
        """
        print("Getting current page jobs…")

        # --- CONSTANTS ---
        # JOB_LIST_CSS         = 'ul[class*="scaffold-layout__list"]'
        JOB_CARD_SELECTOR    = 'li[data-occludable-job-id]'
        DESCRIPTION_CLASS    = 'jobs-description-content'

        # 1) Make sure everything is in the DOM
        self.scroll_all_jobs()

        # 2) Wait for at least one card
        self.wait_till_element_ready(By.CSS_SELECTOR, JOB_CARD_SELECTOR)

        # 3) Grab all the <li> cards
        job_elements = self.driver.find_elements(
            By.CSS_SELECTOR, JOB_CARD_SELECTOR
        )
        total_jobs = len(job_elements)
        print(f"Found {total_jobs} job cards.")

        jobs = []
        for i in range(total_jobs):
            # avoid stale elements
            job_elements = self.driver.find_elements(
                By.CSS_SELECTOR, JOB_CARD_SELECTOR
            )
            job = job_elements[i]

            # click to load details
            self.driver.execute_script(
                "arguments[0].scrollIntoView();",
                job
            )
            job.click()
            time.sleep(self.delay)

            # description
            desc_elems = self.driver.find_elements(
                By.CLASS_NAME, DESCRIPTION_CLASS
            )
            description = " ".join(
                d.text.strip() for d in desc_elems if d.text.strip()
            )

            skills = []
            # try:
            #     skills = self.get_job_skills()
            # except TimeoutException:
            #     skills = []

            
            print(f"Gathering job {i} information...")

            # metadata
            lines = job.text.split("\n")
            position = lines[0] if len(lines) > 0 else ""
            company = lines[2] if len(lines) > 2 else ""
            loc_and_mode = lines[3] if len(lines) > 3 else ""
            try:
                location, work_mode = Scraper.extract_location_and_mode(
                    loc_and_mode
                )
            except ValueError:
                location = work_mode = ""

            jobs.append([
                position,
                company,
                location,
                work_mode,
                description,
                skills
            ])

        return jobs
        

    @retry(TimeoutException, delay=delay) #, tries=tries)
    def get_job_skills(self):
        """
        Click on the skills to displays them in a popup, then extract them.
        """
        print("Getting job skills...")

        # click display skills popup
        self.wait_till_element_ready(By.CLASS_NAME, 'job-details-jobs-unified-top-card__job-insight-text-button')
        view_skills_button = self.driver.find_element(By.CLASS_NAME, 'job-details-jobs-unified-top-card__job-insight-text-button')
        view_skills_button.click()

        # get skills list
        self.wait_till_element_ready(By.CLASS_NAME, "job-details-skill-match-status-list")
        skills_list = self.driver.find_element(By.CLASS_NAME, "job-details-skill-match-status-list")

        # clean skills list
        skills_list_clean = skills_list.text.split('\n')
        skills_list_clean = list(filter(lambda skill: skill != 'Add', skills_list_clean))

        # close the skills list popup
        self.wait_till_element_ready(By.CLASS_NAME, "artdeco-button")
        close_popup_button = self.driver.find_element(By.CLASS_NAME,  "artdeco-button")
        close_popup_button.click()

        return skills_list_clean


    def get_pagination_buttons(self):
        """
        Find the pagination buttons. 
        These buttons are used to navigate through each page.
        """
        print("Getting pagination buttons...")
        self.wait_till_element_ready(By.CLASS_NAME, "jobs-search-pagination__pages")
        pagination = self.driver.find_element(By.CLASS_NAME, "jobs-search-pagination__pages")
        pagination_buttons = pagination.find_elements(By.XPATH, './/button')

        # Debugging
        print(f"Found {len(pagination_buttons)} pagination buttons")
        # print('pagination', pagination)

        return pagination_buttons
    
    
    @staticmethod
    def extract_location_and_mode(input_string):
        """
        Use regex to extract the job location and the work mode (e.g. hybrid).
        """
        # Define the regex pattern to match location and work mode
        pattern = r'([a-zA-Z\s,]+)\s\((\w+)\)'
        
        # Use re.search to find the match
        match = re.search(pattern, input_string)
        
        if match:
            location = match.group(1).strip()
            work_mode = match.group(2).strip()
            return location, work_mode
        else:
            return None, None


    def close_driver(self):
        """
        Close the browser
        """
        self.driver.quit()
