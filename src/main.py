from bot.Scraper import Scraper
import sqlserver
import CSV


import time

import sys
sys.path.append('..')

from selenium.common.exceptions import StaleElementReferenceException
from dotenv import load_dotenv

from bot.Scraper import Scraper
from src.csv import save_to_csv
from src.utils.utils import flatten_jobs_array


def collect_job_data(job_title, job_location, delay=1):
    
    # Search jobs by title and location
    scraper.search_jobs(job_title, job_location)
    time.sleep(delay)

    # Get the  pagination buttons
    pagination_buttons = scraper.get_pagination_buttons()
    print(f"{len(pagination_buttons)} pages found")

    # Loop through each page
    # [:-1] is to ignore the last page as we click on the i+1 button
    all_jobs = []
    for i, button in enumerate(pagination_buttons[:-1]):

        try:
            print("button", button)
            # get the jobs of the current page
            current_page_jobs = scraper.get_current_page_jobs()
            all_jobs.append(current_page_jobs)

            # navigate to the next page
            # button.click()
            # Get the buttons again to avoid a StaleElementReferenceException
            pagination_buttons = scraper.get_pagination_buttons()
            pagination_buttons[i+1].click()

        except StaleElementReferenceException as e:
            print('The was an error...')
            print(e)
        except Exception as e:
            print('The was an error...')
            print(e)

        return all_jobs



if __name__ == 'main':
    # Create a scraper object
    scraper = Scraper(delay=1)

    # Login to LinkedIn
    scraper.login()

    # Collect job data
    job_titles = [
        "data scientist", "llm engineer", "ai engineer", "machine learning engineer", 
        "mlops engineer", "ai developer", "generative ai engineer"
    ]
    job_location = "canada"
    all_jobs = []


    for title in job_titles:
        try:
            print(f"Collecting data for {title}...")
            all_jobs = collect_job_data(title, job_location, delay=2)
            flattened_jobs = flatten_jobs_array(all_jobs)
            columns = ["Job Title", "Company", "City", "Work Mode", "Description"]
            save_to_csv(flattened_jobs, columns, filename=title)
        except Exception as e:
            print(f"An error occurred while collecting data for {title}:")
            print(e)


    # Save to Database
    db = sqlserver()
    conn = db.connect()
    db.save_jobs(conn, all_jobs)
    db.close_connection(conn)

    # Save to CSV file
    CSV.save_to_csv(all_jobs,
                    colnames=['position', 'company', 'location', 'work mode', 'skills', 'description'],
                    filename='jobs.csv')


    # close the browser
    scraper.close_driver()
