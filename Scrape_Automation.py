import streamlit as st

import logging

from link_scrapper import scrapelinksmain
from warc_scraper import warcscrappermain
from pdf_scraper import pdfscrappermain
from token_est import estimate_tokens_in_pdf, estimate_tokens_in_warc

# ---------------------------- Logging Setup ----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------- Streamlit App ----------------------------
st.title("Scrape Automation and Token Estimator")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Link Scraper", "PDF Scraper", "WARC Scraper", "Token Estimator"])

# ---------------------------- Link Scraper Tab ----------------------------
with tab1:
    st.header("Link Scraper")
    
    base_url = st.text_input("Base URL", "", key="link_scraper_base_url", placeholder="https://example.com")
    link_selector = st.text_input("Link Selector (CSS)", "", key="link_scraper_link_selector", placeholder="a.link-class")
    pagination_url = st.text_input("Pagination URL (optional)", "", key="link_scraper_pagination_url", placeholder="https://example.com/page={page_number}")
    next_button_selector = st.text_input("Next Button Selector (optional)", "", key="link_scraper_next_button", placeholder="button.next")
    max_pages = st.number_input("Max Pages", min_value=1, value=1, key="link_scraper_max_pages")
    
    if st.button("Run Link Scraper", key="run_link_scraper"):

        scrapelinksmain(
            base_url=base_url,
            link_selector=link_selector,
            pagination_url=pagination_url,
            next_button_selector=next_button_selector,
            max_pages=max_pages
        )
        
        st.success("Link scraping completed.")

# ---------------------------- PDF Scraper Tab ----------------------------
with tab2:
    st.header("PDF Scrapper")
    
    csv_file = st.text_input("CSV File Path", "", key="pdf_scraper_csv_file", placeholder="C:/path/to/urls.csv")
    output_folder = st.text_input("Output Folder", "", key="pdf_scraper_output_folder", placeholder="output/pdfs")
    
    if st.button("Run PDF Downloader", key="run_pdf_scraper"):

        pdfscrappermain(csv_file, output_folder)

        st.success("PDF scraping completed.")

# ---------------------------- WARC Downloader Tab ----------------------------
with tab3:
    st.header("WARC Scrapper")
    
    csv_file = st.text_input("Path (CSV File Path or Folder Contains CSV)", "", key="warc_scraper_csv_file", placeholder="C:/path/to/urls.csv or folder")
    output_folder = st.text_input("Output Folder", "", key="warc_scraper_output_folder", placeholder="output/warc")
    
    if st.button("Run WARC Downloader", key="run_warc_scraper"):

        warcscrappermain(csv_file, output_folder)

        st.success("WARC scraping completed.")

# ---------------------------- Token Estimator Tab -----------------------------
with tab4:
    st.header("Token Estimator")
    
    file_path = st.text_input("File Path", "", key="token_estimator_file_path", placeholder="C:/path/to/file")
    file_type = st.selectbox("File Type", ["PDF", "WARC"], key="token_estimator_file_type")
    
    if st.button("Estimate Tokens", key="estimate_tokens"):
        if file_type == "PDF":
            # Implement the logic to estimate tokens in PDF
            total_tokens, len_folder = estimate_tokens_in_pdf(file_path)
        elif file_type == "WARC":
            # Implement the logic to estimate tokens in WARC
            total_tokens, len_folder = estimate_tokens_in_warc(file_path)
        
        st.success(f"Total tokens in total {len_folder} {file_type} file: {total_tokens}")