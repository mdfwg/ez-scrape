import os
import csv
import time
from selenium import webdriver
import logging

def setup_webdriver(output_folder):
    # Ensure the output folder exists and is an absolute path
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    options = webdriver.ChromeOptions()
    
    # Additional options to ensure downloads go to the specified folder
    prefs = {
        "download.default_directory": output_folder,  # Absolute path to download directory
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1
    }
    
    # Add experimental options
    options.add_experimental_option("prefs", prefs)
    
    # Additional Chrome options to enforce download behavior
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Create the WebDriver
    driver = webdriver.Chrome(options=options)
    
    return driver

def wait_for_download(path):
    # Wait for downloads to complete
    max_wait_time = 300  # 5 minutes maximum wait
    start_time = time.time()
    
    while True:
        # Check if download is complete (no .crdownload files)
        downloading = any(file.endswith('.crdownload') for file in os.listdir(path))
        
        if not downloading:
            break
        
        # Check for timeout
        if time.time() - start_time > max_wait_time:
            logging.warning("Download timeout occurred")
            break
        
        time.sleep(2)

def scrape_from_list(link_list, output_folder, catname):
    driver = setup_webdriver(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    
    for id, link in enumerate(link_list):
        driver.get(link)
        logging.info(f"{id}/{len(link_list)} - Downloading pdf from {link}")
    wait_for_download(output_folder)

    driver.quit()

def pdfscrappermain(csv_path, project_folder):
    # Set up logging inside the project folder
    logging.basicConfig(filename=os.path.join(project_folder, 'pdf_scraper.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define the output folder for PDFs
    output_folder = os.path.join(project_folder, 'scraped-pdfs')
    
    os.makedirs(output_folder, exist_ok=True)

    # Read the CSV file and extract links
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        link_list = [row[0] for row in reader]
    
    # Call the scrape function to download PDFs
    scrape_from_list(link_list=link_list, output_folder=output_folder, catname=csv_path.split('/')[-1])

