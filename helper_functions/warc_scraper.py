import os
import csv
import time
import requests
import socket
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
import logging
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to save a website to a WARC file
def save_website_to_warc(url, driver, output_folder):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        html = driver.page_source
        response = requests.get(url, verify=False)
        response_headers = response.headers
        content_type = response_headers.get('Content-Type')
        server = response_headers.get('Server', 'Unknown')
        ip_address = socket.gethostbyname(url.split('/')[2])

        request_headers_list = [
            ('Host', url.split('/')[2]),
            ('User-Agent', driver.execute_script("return navigator.userAgent;")),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        ]
        request_status_line = "GET / HTTP/1.1"
        http_request_headers = StatusAndHeaders(request_status_line, request_headers_list, is_http_request=True)

        request_payload = BytesIO()

        sanitized_url = url.split("go.id/")[-1]
        sanitized_url = sanitized_url.replace('.html', '').replace('.htm', '')
        sanitized_url = sanitized_url.replace('/', '_').replace(':', '_')

        warc_writer = WARCWriter(open(os.path.join(output_folder, f'{filename(sanitized_url)}.warc'), 'wb'), gzip=False)
        request_record = warc_writer.create_warc_record(url, 'request', payload=request_payload, http_headers=http_request_headers)
        request_record.rec_headers.add_header('WARC-IP-Address', ip_address)
        warc_writer.write_record(request_record)

        response_status_line = f"HTTP/1.1 {response.status_code} OK"
        response_headers_list = [
            ('Content-Type', content_type),
            ('Server', server),
            ('Connection', 'keep-alive')
        ]
        http_response_headers = StatusAndHeaders(response_status_line, response_headers_list)
        response_payload = BytesIO(html.encode('utf-8'))
        response_record = warc_writer.create_warc_record(url, 'response', payload=response_payload, http_headers=http_response_headers)
        response_record.rec_headers.add_header('WARC-Concurrent-To', request_record.rec_headers.get_header('WARC-Record-ID'))
        response_record.rec_headers.add_header('WARC-IP-Address', ip_address)
        warc_writer.write_record(response_record)

        metadata_content = (f"URL: {url}\nTimestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\nContent-Length: {len(html.encode('utf-8'))}\n").encode('utf-8')
        metadata_record = warc_writer.create_warc_record(uri='urn:uuid:metadata-record', record_type='metadata', payload=BytesIO(metadata_content))
        metadata_record.rec_headers.add_header('WARC-Concurrent-To', response_record.rec_headers.get_header('WARC-Record-ID'))
        warc_writer.write_record(metadata_record)

    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")

# Helper function to create a valid filename
def filename(url):
    return url.split('//')[-1].replace('/', '_').replace(':', '_')

# Function to scrape the list of links and save them as WARC files
def scrape_from_list(link_list, output_folder, catname):
    options = Options()
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)
    os.makedirs(output_folder, exist_ok=True)
    
    for id, link in enumerate(link_list):
        save_website_to_warc(link, driver, output_folder=output_folder)
        logging.info(f"{id}/{len(link_list)} - {catname} - Saved WARC Index {link}")
            
    driver.quit()

# Main function to process the CSV and scrape WARC files
def warcscrappermain(path, project_folder):
    # Set up logging for WARC scraper
    log_dir = os.path.join(project_folder, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(filename=os.path.join(log_dir, 'warc_scraping_error.log'), level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.basicConfig(filename=os.path.join(log_dir, 'warc_scraping_info.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Define output folder for WARC files
    output_folder = os.path.join(project_folder, 'scraped-warcs')
    os.makedirs(output_folder, exist_ok=True)

    # Process the CSV or folder containing CSVs
    if path.endswith('.csv'):
        with open(path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            link_list = [row[0] for row in reader]
        scrape_from_list(link_list=link_list, output_folder=output_folder, catname=path.split('/')[-1])
    else:
        csv_list = [f for f in os.listdir(path) if f.endswith('.csv')]
        for csv_file in csv_list:
            with open(os.path.join(path, csv_file), 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                link_list = [row[0] for row in reader]
            scrape_from_list(link_list=link_list, output_folder=output_folder, catname=csv_file)
