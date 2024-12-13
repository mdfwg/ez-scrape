import os
import logging
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_webdriver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": "/Users/muhammad.galih/Documents/streamlit/output",  # Set download directory
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1  
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def extract_links(driver, link_selector):
    try:
        links = WebDriverWait(driver, 25).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, link_selector))
        )
        links = [link.get_attribute('href') for link in links]
        logging.info(f"Extracted {len(links)} links.")
        return links
    
    except Exception as e:
        logging.error(f"Error extracting links: {e}")
        return []

def scrape_links(driver, pagination_url=None, link_selector='a', next_button_selector=None, max_pages=10):
    links = []

    if pagination_url:
        for page_number in range(1, max_pages + 1):
            page_url = pagination_url.format(page_number=page_number)
            driver.get(page_url)
            links.extend(extract_links(driver, link_selector))
            logging.info(f"Scraped page {page_number}: {page_url}")
            time.sleep(2)
    else:
        current_page = 1
        while current_page <= max_pages:
            links.extend(extract_links(driver, link_selector))
            logging.info(f"Scraped page {current_page}")
            try:
                if next_button_selector:
                    next_button_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button_element)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button_element)
                    current_page += 1
                    time.sleep(2)
                else:
                    logging.info("No next button or pagination URL found. Stopping scraping.")
                    break
            except Exception as e:
                logging.warning(f"Error or no next button: {e}. Stopping scraping.")
                break

    return links

def save_links_to_csv(links, csv_file):
    df = pd.DataFrame(links)
    df = df.rename(columns={0: 'link'})
    df.to_csv(csv_file, index=False)
    logging.info(f"Saved {len(links)} links to {csv_file}")

def scrapelinksmain(base_url, link_selector, pagination_url=None, next_button_selector=None, max_pages=5):
    driver = setup_webdriver()
    try:
        logging.info(f"Scraping website: {base_url}")
        driver.get(base_url)
        all_links = scrape_links(driver, pagination_url, link_selector, next_button_selector, max_pages)
        # make a csv name with time stamp
        csv_file = f"{time.strftime('%Y-%m-%d-%H:%M')}_{base_url.removeprefix('https://').split('/')[0]}_links.csv"
        save_links_to_csv(all_links, os.path.join("/Users/muhammad.galih/Documents/streamlit/output/links/", csv_file))
    finally:
        driver.quit()