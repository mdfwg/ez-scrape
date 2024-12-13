import os
import csv
import time
from selenium import webdriver
import logging

def setup_webdriver(output_folder):
    options = webdriver.ChromeOptions()
    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": output_folder,  # Set download directory
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1  
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def wait_for_download(path):
    while any(file.endswith('.crdownload') for file in os.listdir(path)):
        time.sleep(2)

def scrape_from_list(link_list, output_folder, catname):

    driver = setup_webdriver(output_folder)
    os.makedirs(output_folder, exist_ok=True)
    
    for id, link in enumerate(link_list):
        driver.get(link)
        logging.info(f"{id}/{len(link_list)} - Downloading pdf from {link}")
    wait_for_download(output_folder)

    driver.quit()

def pdfscrappermain(csv_path, output_folder='/Users/muhammad.galih/Documents/streamlit/output/pdfs'):
    os.makedirs(output_folder, exist_ok=True)

    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        link_list = [row[0] for row in reader]
    scrape_from_list(link_list=link_list, output_folder=output_folder, catname=csv_path.split('/')[-1])