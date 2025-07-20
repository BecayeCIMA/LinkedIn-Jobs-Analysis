# LinkedIn Jobs Analysis

**Exploring trends in Data Science job postings using automation, language models, and Power BI.**

### Motivation

While exploring internship opportunities in Data Science, I wanted to better understand which skills and tools were in demand — across roles, industries, and locations. Instead of manually combing through countless job listings, I built a lightweight research pipeline to help me extract and visualize this information efficiently.

### Approach

The project follows a three-step workflow:

1. **Browser Automation**
   Using **Selenium**, I automated the navigation of publicly available job listings to extract posting content for analysis — just like a user browsing at scale.

   > *Note: This was done respectfully, with rate-limiting and care to avoid violating LinkedIn’s terms.*

2. **Natural Language Processing with LLMs**
   Job descriptions were passed through **open-source language models** (via [Ollama](https://ollama.com)) to extract structured data like:

   * Required skills
   * Years of experience
   * Educational background
   * Tools and frameworks mentioned
   * Role specializations (e.g. NLP, GenAI)

3. **Visualization in Power BI**
   The structured job data was loaded into **SQL Server**, then visualized in **Power BI** dashboards — revealing patterns and trends across hundreds of postings.

### Tools Used

* **Python**
* **Selenium** for browser automation
* **LLMs via Ollama** for parsing unstructured descriptions
* **SQL Server** for data storage
* **Power BI** for data visualization

### Key Results

* Extracted and analyzed job requirements from a diverse set of Data Science roles
* Identified key skills and tools employers are seeking (e.g. Python, LLMs, cloud platforms)
* Gained personal insights to guide my learning and application strategy


<img width="946" alt="image" src="https://user-images.githubusercontent.com/87549214/232181049-bd6870ee-613c-4985-b937-ac9a23ea7d73.png">



## Code Structure

```
src/
│
├── main.py
│   ↳ Entry point for the project. Coordinates the scraping, parsing, and data storage pipeline.
│
├── bot/
│   └── Scraper.py
│       ↳ Automates interaction with LinkedIn using Selenium to collect job postings.
│
├── database/
│   ├── sqlserver.py
│   │   ↳ Manages connection to the SQL Server database and handles data insertion.
│   └── csv.py
│       ↳ Provides utility functions to save job data locally in CSV format.
│
└── utils/
    ↳ Helpers functions.
```

## How to use it

1. Clone the repo
```
git clone https://github.com/BecayeSoft/LinkedIn-Jobs-Analysis.git
cd LinkedIn-Jobs-Analysis
```

2. Install the requirements in a virtual environment

```bash
python -m venv .venv  
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. Set your credentials

Create a file named ".env" and add your credentials.
Make sure to replace "youremail" and "yourpassword" with your LinkedIn credentials.

```plaintext
EMAIL=youremail
PASSWORD=yourpassword
```

4. Run

You can use the notebooks for a more interactive experience, or run the main script directly.
Change the job titles and the location according to your needs in the notebook or in the main file.


### References

Thanks to <a href="https://medium.com/nerd-for-tech/linked-in-web-scraper-using-selenium-15189959b3ba">Matan Freedman</a> for its tutorial on Selenium and LinkedIn scraping
