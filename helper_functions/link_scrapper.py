import os
import logging
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging to log into project-specific folder
def setup_webdriver(project_folder):
    options = webdriver.ChromeOptions()
    prefs = {
        "download.prompt_for_download": False,
        "download.default_directory": os.path.join(project_folder, 'links'),  # Set download directory in project folder
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1  
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)
    return driver

def extract_links(driver, link_selector):
    """Extracts links using the provided CSS selector."""
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

def scroll_to_load(driver, max_scrolls=10, wait_time=2):
    """Gradually scroll down the page to load dynamic content."""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        no_new_content_count = 0  # Track how many times we encounter no new content

        for _ in range(max_scrolls):
            # Scroll down by a fixed amount
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(wait_time)  # Wait for content to load

            # Check if the page height has changed
            new_height = driver.execute_script("return document.body.scrollHeight")

            # If no new content is loaded (page height hasn't changed), increment the counter
            if new_height == last_height:
                no_new_content_count += 1
                logging.info(f"Scrolled but no new content found. Attempt {no_new_content_count} of {max_scrolls}.")
                if no_new_content_count >= 5:  # Stop after 5 unsuccessful scroll attempts
                    logging.info("No new content loaded after multiple scroll attempts. Stopping.")
                    break
            else:
                last_height = new_height  # Update the height if new content has loaded
                no_new_content_count = 0  # Reset counter if new content is found

    except Exception as e:
        logging.error(f"Error while scrolling: {e}")

def click_load_more_button(driver, button_selector):
    """Clicks the 'Load More' button to load additional content."""
    try:
        load_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", load_more_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", load_more_button)
        logging.info("Clicked 'Load More' button.")
        time.sleep(2)  # Adjust based on how long it takes for new content to load
    except Exception as e:
        logging.warning(f"Error clicking 'Load More' button: {e}")
        return False  # Return False if there is no button or an error occurs
    return True

def scrape_links(driver, pagination_url=None, link_selector='a', next_button_selector=None, max_pages=10, 
                 scroll_to_load_more=False, load_more_button_selector=None, max_no_new_links=5):
    links = set()  # Using a set to prevent duplicate links
    new_links_count = 0  # Count the number of new links found in each iteration
    load_more_attempts = 0
    last_found_links = set()  # To track previously found links

    if pagination_url:
        # Pagination scraping logic (same as before)
        for page_number in range(1, max_pages + 1):
            page_url = pagination_url.format(page_number=page_number)
            driver.get(page_url)
            current_links = extract_links(driver, link_selector)
            new_links = set(current_links) - last_found_links  # Find new links by comparing with the last iteration
            links.update(new_links)
            last_found_links.update(current_links)
            logging.info(f"Scraped page {page_number}: {page_url}")
            logging.info(f"New links found on this page: {len(new_links)}")
            if not new_links:
                new_links_count += 1
            else:
                new_links_count = 0  # Reset if new links are found

            if new_links_count >= max_no_new_links:  # Stop after 5 iterations with no new links
                logging.info(f"No new links found after {max_no_new_links} attempts. Stopping scraping.")
                break
            time.sleep(2)
    else:
        current_page = 1
        while current_page <= max_pages:
            # Always check and click "Load More" button if it exists
            if load_more_button_selector:
                load_more_button_exists = click_load_more_button(driver, load_more_button_selector)
                if load_more_button_exists:
                    current_links = extract_links(driver, link_selector)
                    new_links = set(current_links) - last_found_links  # Check for new links
                    links.update(new_links)
                    last_found_links.update(current_links)
                    logging.info(f"Clicked 'Load More' button and found {len(new_links)} new links.")
                    load_more_attempts = 0  # Reset the load more attempts counter
                else:
                    load_more_attempts += 1
                    logging.info(f"No 'Load More' button found. Attempts: {load_more_attempts}")
                    if load_more_attempts >= 5:  # Stop after 5 failed attempts to find the 'Load More' button
                        logging.info("No more 'Load More' buttons found after 5 attempts. Stopping scraping.")
                        break

            # If scroll to load more is enabled
            if scroll_to_load_more:
                scroll_to_load(driver)  # Scroll gradually and try to load new content
                current_links = extract_links(driver, link_selector)
                new_links = set(current_links) - last_found_links  # Check for new links
                links.update(new_links)
                last_found_links.update(current_links)
                logging.info(f"Scrolled and found {len(new_links)} new links.")
                if not new_links:
                    new_links_count += 1
                else:
                    new_links_count = 0  # Reset if new links are found

                if new_links_count >= max_no_new_links:  # Stop after 5 iterations with no new links
                    logging.info(f"No new links found after {max_no_new_links} attempts. Stopping scraping.")
                    break

            logging.info(f"Scraped page {current_page}")
            time.sleep(2)
            current_page += 1  # Increment the page number

            # If we are scraping without a pagination URL, we need to handle the next button (if applicable)
            if next_button_selector:
                try:
                    next_button_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector))
                    )
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button_element)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", next_button_element)
                    current_page += 1
                    time.sleep(2)
                except Exception as e:
                    logging.warning(f"Error or no next button: {e}. Stopping scraping.")
                    break

    return list(links)  # Convert the set back to a list to save

def save_links_to_csv(links, project_folder):
    # No need to create a nested 'links' folder, just use the provided folder
    os.makedirs(project_folder, exist_ok=True)  # Ensure the folder exists
    
    # Save links as a CSV with a static name 'links.csv'
    csv_file = 'links.csv'  # Static file name
    df = pd.DataFrame(links)
    df = df.rename(columns={0: 'link'})  # Rename the first column to 'link'
    
    # Save directly to the provided folder
    df.to_csv(os.path.join(project_folder, csv_file), index=False)
    logging.info(f"Saved {len(links)} links to {csv_file}")

def scrapelinksmain(project_folder, base_url, link_selector, pagination_url=None, next_button_selector=None, 
                    max_pages=5, scroll_to_load_more=False, load_more_button_selector=None):
    # Set up logging for this specific project
    logging.basicConfig(filename=os.path.join(project_folder, 'link_scraper.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    driver = setup_webdriver(project_folder)
    try:
        logging.info(f"Scraping website: {base_url}")
        driver.get(base_url)
        
        all_links = scrape_links(
            driver, 
            pagination_url=pagination_url, 
            link_selector=link_selector, 
            next_button_selector=next_button_selector, 
            max_pages=max_pages,
            scroll_to_load_more=scroll_to_load_more,
            load_more_button_selector=load_more_button_selector
        )
        
        # Save links to a CSV file in the project's links folder
        save_links_to_csv(all_links, project_folder)
    finally:
        driver.quit()
