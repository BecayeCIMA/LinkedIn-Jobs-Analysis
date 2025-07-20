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


class ScraperNew:

    delay = 3

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


    def search_jobs(self, position, location=None):
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
        # LinkedIn has a new AI-powered search which changes the interfaces
        # this is why we use a try to ensure the location bar exists
        try:
            search_by_location_bar = search_bars[3]
            search_by_location_bar.clear()                        # clear existing text
            search_by_location_bar.send_keys(location)
        except IndexError:
            print("Location search bar not found.")
        
        # Submit the search
        search_by_keyword_bar.send_keys(Keys.RETURN)


    def get_visible_job_selector(self):
        """
        Returns a tuple: (scroll container WebElement, CSS selector for job cards),
        compatible with both classic and AI-powered search layouts.
        """
        driver = self.driver

        # --- Classic layout ---
        classic_cards = driver.find_elements(By.CSS_SELECTOR, 'li[data-occludable-job-id]')
        if classic_cards:
            print("Layout detected: Classic")
            scroll_container = driver.find_element(
                By.XPATH, '//ul[li[@data-occludable-job-id]]'
            )
            return scroll_container, 'li[data-occludable-job-id]'

        # --- AI-powered layout ---
        ai_cards = driver.find_elements(By.CSS_SELECTOR, 'li[class*="semantic-search-results-list__list-item"]')
        if ai_cards:
            print("Layout detected: AI-powered")
            scroll_container = driver.find_element(
                By.XPATH, '//ul[contains(@class, "semantic-search-results-list")]'
            )
            return scroll_container, 'li[class*="semantic-search-results-list__list-item"]'

        raise RuntimeError("No recognizable job card layout found.")


    def scroll_all_jobs(self):
        """
        Scrolls the job list container to load all lazy-loaded job cards.
        """
        print("Scrolling all job listings...")

        scroll_container, job_card_selector = self.get_visible_job_selector()
        prev_count = -1

        while True:
            self.driver.execute_script(
                "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                scroll_container
            )
            time.sleep(self.delay)

            current_count = len(self.driver.find_elements(
                By.CSS_SELECTOR, job_card_selector
            ))
            print(f"  → {current_count} cards loaded so far…")

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

        # Scroll fully
        self.scroll_all_jobs()

        # Get container + job selector based on layout
        _, job_card_selector = self.get_visible_job_selector()

        # Wait for cards
        self.wait_till_element_ready(By.CSS_SELECTOR, job_card_selector)

        # Get all job elements
        job_elements = self.driver.find_elements(By.CSS_SELECTOR, job_card_selector)
        total_jobs = len(job_elements)
        print(f"Found {total_jobs} job cards.")

        jobs = []
        for i in range(total_jobs):
            # avoid stale elements
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, job_card_selector)
            job = job_elements[i]

            self.driver.execute_script("arguments[0].scrollIntoView();", job)
            job.click()
            time.sleep(self.delay)

            # description
            desc_elems = self.driver.find_elements(By.CLASS_NAME, "jobs-description-content")
            description = " ".join(
                d.text.strip() for d in desc_elems if d.text.strip()
            )

            # Get skills
            try:
                skills = self.get_job_skills()
            except TimeoutException:
                skills = []

            print(f"Gathering job {i} information...")

            # metadata
            lines = job.text.split("\n")
            position = lines[0] if len(lines) > 0 else ""
            company = lines[2] if len(lines) > 2 else ""
            loc_and_mode = lines[3] if len(lines) > 3 else ""
            try:
                location, work_mode = ScraperNew.extract_location_and_mode(loc_and_mode)
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
